"""Sections (Student Groups) across academic years.

Sections keep their names from one year to the next ("Grade 1 A"), so a
group document is re-pointed at the new academic year instead of being
recreated. Before its members are replaced, the section each student sat in
is written onto their Program Enrollment for that year. From then on the
enrollment, not the group, is the record of who was in which section in a
past year, and :func:`get_group_members` answers either way.
"""

import frappe
from frappe import _
from frappe.utils import cint

from education.education.lifecycle.common import (
	branch_of_section,
	clean_spaces,
	split_program,
)


def enrollment_has_section_field():
	return frappe.get_meta("Program Enrollment").has_field("student_group")


def group_has_branch_field():
	return frappe.get_meta("Student Group").has_field("branch")


def section_key(name):
	"""Spacing- and case-insensitive key: "Grade 10A" == "grade 10 a"."""
	return clean_spaces(name).replace(" ", "").lower()


def load_groups():
	"""Every Student Group as {name: row}, with its branch worked out."""
	fields = ["name", "program", "academic_year", "disabled", "batch"]
	has_branch = group_has_branch_field()
	if has_branch:
		fields.append("branch")
	groups = {}
	for row in frappe.get_all("Student Group", fields=fields, limit_page_length=0):
		row.branch = branch_of_section(row.name, row.get("branch") if has_branch else None)
		groups[row.name] = row
	return groups


def resolve_section(name, groups, by_key=None):
	"""Map a section as somebody typed it to an existing group name.

	Returns the group's name, or None when no group matches.
	"""
	name = clean_spaces(name)
	if not name:
		return None
	if name in groups:
		return name
	if by_key is None:
		by_key = {section_key(g): g for g in groups}
	return by_key.get(section_key(name))


def get_group_members(student_group, academic_year=None):
	"""Students of a section for an academic year, as {student: active}.

	For the year the group currently serves, that is its member table. For
	any earlier year it is the submitted enrollments that recorded this
	section, since the member table has moved on to the new class.
	"""
	group_year = frappe.db.get_value("Student Group", student_group, "academic_year")
	if not academic_year or academic_year == group_year or not enrollment_has_section_field():
		rows = frappe.get_all(
			"Student Group Student",
			filters={"parent": student_group, "parenttype": "Student Group"},
			fields=["student", "active"],
		)
		return {row.student: cint(row.active) for row in rows}

	rows = frappe.get_all(
		"Program Enrollment",
		filters={"student_group": student_group, "academic_year": academic_year, "docstatus": 1},
		pluck="student",
	)
	return {student: 1 for student in rows}


def archive_sections(academic_year):
	"""Record each student's current section on their enrollment for the year.

	Only enrollments with no section yet are filled, so running this again
	never overwrites what an earlier run (or a person) recorded. Returns
	(updated, members_without_enrollment).
	"""
	if not enrollment_has_section_field():
		frappe.throw(_("Program Enrollment has no Section field yet. Run bench migrate first."))

	members = frappe.db.sql(
		"""
		SELECT sgs.student, sgs.parent AS student_group, sgs.active
		FROM `tabStudent Group Student` sgs
		JOIN `tabStudent Group` sg ON sg.name = sgs.parent
		WHERE sgs.parenttype = 'Student Group' AND sg.academic_year = %s
		ORDER BY sgs.active DESC, sgs.modified DESC
		""",
		(academic_year,),
		as_dict=True,
	)
	section_of = {}
	for row in members:
		# Active membership wins over an old inactive one.
		section_of.setdefault(row.student, row.student_group)

	enrollments = frappe.get_all(
		"Program Enrollment",
		filters={"academic_year": academic_year, "docstatus": 1},
		fields=["name", "student", "student_group"],
		limit_page_length=0,
	)
	enrolled = set()
	updated = 0
	for enrollment in enrollments:
		enrolled.add(enrollment.student)
		section = section_of.get(enrollment.student)
		if section and not enrollment.student_group:
			frappe.db.set_value(
				"Program Enrollment", enrollment.name, "student_group", section, update_modified=False
			)
			updated += 1

	orphans = sorted(s for s in section_of if s not in enrolled)
	return updated, orphans


def ensure_section(name, program, academic_year, branch=None):
	"""Make sure a section exists, creating it for ``academic_year`` if not.

	An existing group is returned untouched, whatever year it serves: moving
	it onto the new year is the rollover's job, done once every student has
	been enrolled. Returns (group_name, created).
	"""
	groups = load_groups()
	existing = resolve_section(name, groups)
	if existing:
		return existing, False

	base, _suffix = split_program(program)
	group = frappe.new_doc("Student Group")
	group.student_group_name = clean_spaces(name)
	group.group_based_on = "Batch"
	group.program = program
	group.academic_year = academic_year
	if frappe.db.exists("Student Batch Name", base):
		group.batch = base
	if group_has_branch_field():
		group.branch = branch or branch_of_section(name)
	group.flags.ignore_permissions = True
	group.insert()
	return group.name, True


def roll_over_groups(previous_year, new_year, disable_unused=False):
	"""Point every section used in ``new_year`` at that year's students.

	1. Last year's membership is archived onto last year's enrollments.
	2. Each section named on a submitted ``new_year`` enrollment is moved to
	   ``new_year`` (if it still served an earlier year), its program is set to
	   the program most of its new students are in, and its members are
	   replaced by those students, numbered alphabetically.
	3. Students placed in a new-year section are marked inactive in any
	   ``previous_year`` section that was not carried over.
	4. Sections from ``previous_year`` that nobody was placed in are listed,
	   and disabled only when asked.

	Homeroom teachers and instructors are left as they are; reassigning
	teachers is a separate decision. Returns a summary dict.
	"""
	archived, orphans = archive_sections(previous_year)

	enrollments = frappe.db.sql(
		"""
		SELECT pe.student, pe.program, pe.student_group, s.student_name, s.enabled
		FROM `tabProgram Enrollment` pe
		JOIN `tabStudent` s ON s.name = pe.student
		WHERE pe.academic_year = %s AND pe.docstatus = 1
		  AND IFNULL(pe.student_group, '') != ''
		""",
		(new_year,),
		as_dict=True,
	)
	by_section = {}
	for row in enrollments:
		by_section.setdefault(row.student_group, []).append(row)

	summary = frappe._dict(
		archived=archived,
		members_without_enrollment=len(orphans),
		rolled_over=[],
		synced=[],
		program_changed=[],
		mixed_programs=[],
		skipped=[],
		unused=[],
		disabled=[],
	)

	for section, students in sorted(by_section.items()):
		group = frappe.get_doc("Student Group", section)
		if group.academic_year not in (new_year, previous_year) and group.academic_year:
			# Serving some other year: leave it for a person to sort out.
			start = frappe.db.get_value("Academic Year", group.academic_year, "year_start_date")
			new_start = frappe.db.get_value("Academic Year", new_year, "year_start_date")
			if start and new_start and start > new_start:
				summary.skipped.append(section)
				continue

		if group.academic_year != new_year:
			group.academic_year = new_year
			summary.rolled_over.append(section)
		else:
			summary.synced.append(section)

		program_counts = {}
		for row in students:
			program_counts[row.program] = program_counts.get(row.program, 0) + 1
		majority = max(program_counts.items(), key=lambda item: item[1])[0]
		if len(program_counts) > 1:
			summary.mixed_programs.append(
				"{0}: {1}".format(
					section, ", ".join(f"{p} ({n})" for p, n in sorted(program_counts.items()))
				)
			)
		if group.program != majority:
			summary.program_changed.append(f"{section}: {group.program} -> {majority}")
			group.program = majority
			base = split_program(majority)[0]
			if group.group_based_on == "Batch" and frappe.db.exists("Student Batch Name", base):
				group.batch = base

		group.set("students", [])
		for number, row in enumerate(sorted(students, key=lambda r: (r.student_name or "").lower()), 1):
			group.append(
				"students",
				{
					"student": row.student,
					"student_name": row.student_name,
					"group_roll_number": number,
					"active": 1 if cint(row.enabled) else 0,
				},
			)
		if group.disabled:
			group.disabled = 0
		group.flags.ignore_permissions = True
		group.save()

	# Students now placed in a new-year section stop being active in last
	# year's sections that were not carried over. The rows stay (and the
	# section is already recorded on last year's enrollment); only "active"
	# changes, so lookups of a student's current section find the new one.
	placed = {row.student for row in enrollments}
	stale = frappe.db.sql(
		"""
		SELECT sgs.name, sgs.student
		FROM `tabStudent Group Student` sgs
		JOIN `tabStudent Group` sg ON sg.name = sgs.parent
		WHERE sgs.parenttype = 'Student Group' AND sgs.active = 1 AND sg.academic_year = %s
		""",
		(previous_year,),
		as_dict=True,
	)
	summary.deactivated = 0
	for row in stale:
		if row.student in placed:
			frappe.db.set_value("Student Group Student", row.name, "active", 0, update_modified=False)
			summary.deactivated += 1

	used = set(by_section)
	for name in frappe.get_all(
		"Student Group", filters={"academic_year": previous_year, "disabled": 0}, pluck="name"
	):
		if name in used:
			continue
		summary.unused.append(name)
		if disable_unused:
			frappe.db.set_value("Student Group", name, "disabled", 1)
			summary.disabled.append(name)

	return summary
