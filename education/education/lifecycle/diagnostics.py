"""Everything about students, applications, enrollments and sections that is
out of step, as one flat list.

The reconciliation rows (see ``reconcile``) contribute their issues; the
checks below cover what reconciliation cannot see from one student at a
time: records that contradict each other, sections whose members do not
match the enrollments, logins pointing at the wrong place, and so on.

Every finding is a dict:
    severity   Blocked / Review / Info
    category   Identity, Promotion, Section, Enrollment, Exit, Account, Exam,
               Status, Data Quality
    issue      what is wrong
    action     what to do about it
    student, student_name, school_id, student_applicant, previous_program,
    new_program, section, branch, reference_doctype, reference_name
"""

import frappe
from frappe import _
from frappe.utils import cint

from education.education.lifecycle.common import (
	BLOCKED,
	INFO,
	REVIEW,
	SEVERITY_RANK,
	normalize_name,
)
from education.education.lifecycle.reconcile import (
	ALREADY_ENROLLED,
	GRADUATING,
	NOT_RETURNING,
	Context,
	build_rows,
)

SUGGESTED_ACTION = {
	"Identity": _("Correct the School ID or name on the application or student record"),
	"Promotion": _("Correct the application's program or the Not Promoted list"),
	"Section": _("Fix the roster or the section on the enrollment"),
	"Enrollment": _("Open the enrollment and correct, submit or cancel it"),
	"Exit": _("Record a Student Exit, or readmit through the enrollment tool"),
	"Status": _("Confirm the restriction is still meant to apply"),
	"Account": _("Run the Student User Creation Tool for this student"),
	"Exam": _("Enter or correct the External Exam Result"),
	"Data Quality": _("Review and merge or correct the records"),
}


def _finding(severity, category, issue, **extra):
	row = frappe._dict(
		severity=severity,
		category=category,
		issue=issue,
		action=SUGGESTED_ACTION.get(category, ""),
		student="",
		student_name="",
		school_id="",
		student_applicant="",
		previous_program="",
		new_program="",
		section="",
		branch="",
		reference_doctype="",
		reference_name="",
	)
	row.update(extra)
	return row


def _student_bits(student):
	return {
		"student": student.name,
		"student_name": student.student_name,
		"school_id": student.custom_school_id,
	}


def collect(new_year, previous_year, branch=None, program=None):
	"""All findings for the new year, with last year as the comparison point."""
	ctx = Context(previous_year, new_year)
	findings = []

	rows, _summary = build_rows(
		previous_year,
		new_year,
		program=program,
		branch=branch,
		include_enrolled=True,
		include_not_returning=True,
		ctx=ctx,
	)
	for row in rows:
		base = {
			"student": row.student,
			"student_name": row.student_name,
			"school_id": row.school_id,
			"student_applicant": row.student_applicant,
			"previous_program": row.previous_program,
			"new_program": row.new_program,
			"section": row.new_section or row.previous_section,
			"branch": row.branch,
		}
		for issue in row.issue_list:
			if (
				issue["category"] == "Section"
				and issue["severity"] == INFO
				and row.status != ALREADY_ENROLLED
			):
				# Notes about the registration page's suggested section; they
				# only matter in the enrollment tool, once a roster is loaded.
				continue
			findings.append(_finding(issue["severity"], issue["category"], issue["message"], **base))
		if row.status == NOT_RETURNING:
			findings.append(
				_finding(
					INFO,
					"Exit",
					_("Enrolled in {0} with no application for {1}").format(previous_year, new_year),
					**base,
				)
			)
		elif row.status == GRADUATING:
			findings.append(
				_finding(
					INFO,
					"Exit",
					_("Finished Grade 12 in {0}; record the graduation").format(previous_year),
					**base,
				)
			)

	# Checks that do not depend on a filtered program are skipped when the
	# report is narrowed to one program, so its numbers stay comparable.
	if not program:
		findings += _student_record_checks(ctx, branch)
		findings += _enrollment_checks(ctx, branch)
		findings += _section_checks(ctx, branch)
		findings += _account_checks(ctx, branch)
		findings += _exam_checks(ctx, branch)

	findings.sort(
		key=lambda f: (
			SEVERITY_RANK.get(f.severity, 9),
			f.category,
			f.new_program or f.previous_program or "",
			(f.student_name or "").lower(),
		)
	)
	return findings


def _in_branch(ctx, student, branch):
	return not branch or ctx.branch_of(student) == branch


def _student_record_checks(ctx, branch):
	findings = []
	for student in ctx.students.values():
		if not _in_branch(ctx, student, branch):
			continue
		bits = _student_bits(student)
		exit_row = ctx.open_exits.get(student.name)
		if exit_row and cint(student.enabled):
			findings.append(
				_finding(
					REVIEW,
					"Exit",
					_("Has exit {0} but the student record is still enabled").format(exit_row.name),
					reference_doctype="Student Exit",
					reference_name=exit_row.name,
					**bits,
				)
			)
		elif not exit_row and student.date_of_leaving and cint(student.enabled):
			findings.append(
				_finding(
					REVIEW,
					"Exit",
					_("Has a leaving date but is still enabled and has no exit record"),
					**bits,
				)
			)
		elif not exit_row and not cint(student.enabled):
			findings.append(
				_finding(
					INFO,
					"Exit",
					_("Disabled with no exit record; record why the student left"),
					**bits,
				)
			)

	# Same person entered twice: identical normalised name and date of birth.
	seen = {}
	for row in frappe.get_all(
		"Student", fields=["name", "student_name", "date_of_birth"], limit_page_length=0
	):
		if not row.date_of_birth:
			continue
		seen.setdefault((normalize_name(row.student_name), str(row.date_of_birth)), []).append(row.name)
	for (_name, _dob), names in seen.items():
		if len(names) < 2:
			continue
		for name in names:
			student = ctx.students.get(name)
			if not student or not _in_branch(ctx, student, branch):
				continue
			findings.append(
				_finding(
					REVIEW,
					"Data Quality",
					_("Same name and date of birth as {0}; possibly the same child twice").format(
						", ".join(n for n in names if n != name)
					),
					**_student_bits(student),
				)
			)
	return findings


def _enrollment_checks(ctx, branch):
	findings = []
	for year, enrollments in ((ctx.previous_year, ctx.prev_enrollments), (ctx.new_year, ctx.new_enrollments)):
		for student_name, rows in enrollments.items():
			student = ctx.students.get(student_name)
			if not student or not _in_branch(ctx, student, branch):
				continue
			bits = _student_bits(student)
			submitted = [r for r in rows if r.docstatus == 1]
			if year == ctx.previous_year and len(submitted) > 1:
				# Reported per row by reconciliation for returning students;
				# here for everyone else.
				if student.sid not in ctx.applicants_by_sid:
					findings.append(
						_finding(
							REVIEW,
							"Enrollment",
							_("Enrolled more than once in {0}: {1}").format(
								year, ", ".join(r.name for r in submitted)
							),
							**bits,
						)
					)
			if year == ctx.new_year:
				if not cint(student.enabled):
					findings.append(
						_finding(
							REVIEW,
							"Enrollment",
							_("Enrolled in {0} but the student record is disabled").format(year),
							reference_doctype="Program Enrollment",
							reference_name=rows[0].name,
							new_program=rows[0].program,
							**bits,
						)
					)
				if student.sid not in ctx.applicants_by_sid:
					findings.append(
						_finding(
							REVIEW,
							"Enrollment",
							_("Enrolled in {0} without an application for that year").format(year),
							reference_doctype="Program Enrollment",
							reference_name=rows[0].name,
							new_program=rows[0].program,
							**bits,
						)
					)
	# Drafts from last year never became real enrollments.
	for row in frappe.get_all(
		"Program Enrollment",
		filters={"academic_year": ctx.previous_year, "docstatus": 0},
		fields=["name", "student", "program"],
		limit_page_length=0,
	):
		student = ctx.students.get(row.student)
		if student and not _in_branch(ctx, student, branch):
			continue
		findings.append(
			_finding(
				REVIEW,
				"Enrollment",
				_("Draft enrollment from {0} was never submitted").format(ctx.previous_year),
				reference_doctype="Program Enrollment",
				reference_name=row.name,
				previous_program=row.program,
				**(_student_bits(student) if student else {"student": row.student}),
			)
		)
	return findings


def _section_checks(ctx, branch):
	"""Sections serving the new year (or last year, until they are rolled over)."""
	findings = []
	year_groups = {
		name: g
		for name, g in ctx.groups.items()
		if g.academic_year in (ctx.new_year, ctx.previous_year) and not cint(g.disabled)
	}
	if branch:
		year_groups = {n: g for n, g in year_groups.items() if g.branch == branch}
	if not year_groups:
		return findings

	members = frappe.get_all(
		"Student Group Student",
		filters={"parent": ["in", list(year_groups)], "parenttype": "Student Group"},
		fields=["parent", "student", "active"],
		limit_page_length=0,
	)
	active_groups = {}
	group_programs = {}
	for m in members:
		group = year_groups[m.parent]
		student = ctx.students.get(m.student)
		if not student:
			continue
		bits = _student_bits(student)
		if cint(m.active):
			active_groups.setdefault((m.student, group.academic_year), []).append(m.parent)
			if not cint(student.enabled):
				findings.append(
					_finding(
						REVIEW,
						"Section",
						_("Disabled student is still active in {0}").format(m.parent),
						section=m.parent,
						reference_doctype="Student Group",
						reference_name=m.parent,
						**bits,
					)
				)
		enrollments = (
			ctx.new_enrollments if group.academic_year == ctx.new_year else ctx.prev_enrollments
		).get(m.student, [])
		programs = {e.program for e in enrollments if e.docstatus == 1}
		group_programs.setdefault(m.parent, {})
		for p in programs:
			group_programs[m.parent][p] = group_programs[m.parent].get(p, 0) + 1
		if cint(m.active) and not programs:
			findings.append(
				_finding(
					REVIEW,
					"Section",
					_("Member of {0} but not enrolled in {1}").format(m.parent, group.academic_year),
					section=m.parent,
					reference_doctype="Student Group",
					reference_name=m.parent,
					**bits,
				)
			)
		elif cint(m.active) and group.program and group.program not in programs:
			findings.append(
				_finding(
					REVIEW,
					"Section",
					_("In {0} ({1}) but enrolled in {2}").format(
						m.parent, group.program, ", ".join(sorted(programs))
					),
					section=m.parent,
					reference_doctype="Student Group",
					reference_name=m.parent,
					**bits,
				)
			)

	for (student_name, year), groups in active_groups.items():
		if len(groups) < 2:
			continue
		findings.append(
			_finding(
				REVIEW,
				"Section",
				_("Active in more than one section for {0}: {1}").format(year, ", ".join(sorted(groups))),
				section=", ".join(sorted(groups)),
				**_student_bits(ctx.students[student_name]),
			)
		)

	for group_name, programs in group_programs.items():
		if len(programs) > 1:
			findings.append(
				_finding(
					REVIEW,
					"Section",
					_("Section {0} mixes programs: {1}").format(
						group_name, ", ".join(f"{p} ({n})" for p, n in sorted(programs.items()))
					),
					section=group_name,
					reference_doctype="Student Group",
					reference_name=group_name,
				)
			)

	# Enrolled in the new year but not placed in any of its sections.
	new_year_sections = {n for n, g in year_groups.items() if g.academic_year == ctx.new_year}
	if new_year_sections:
		placed = {s for (s, year) in active_groups if year == ctx.new_year}
		for student_name, rows in ctx.new_enrollments.items():
			if student_name in placed or not any(r.docstatus == 1 for r in rows):
				continue
			student = ctx.students.get(student_name)
			if not student or not _in_branch(ctx, student, branch):
				continue
			findings.append(
				_finding(
					INFO,
					"Section",
					_("Enrolled in {0} but not in any of its sections yet").format(ctx.new_year),
					new_program=rows[0].program,
					section=rows[0].get("student_group") or "",
					**_student_bits(student),
				)
			)
	return findings


def _account_checks(ctx, branch):
	from education.education.api import _resolve_student_email

	findings = []
	users = {
		row.name: row
		for row in frappe.get_all(
			"User",
			filters={"user_type": "Website User"},
			fields=["name", "enabled"],
			limit_page_length=0,
		)
	}
	for row in frappe.get_all(
		"Student",
		fields=["name", "student_name", "custom_school_id", "student_email_id", "user", "enabled"],
		limit_page_length=0,
	):
		student = ctx.students.get(row.name)
		if not cint(row.enabled) or not student or not _in_branch(ctx, student, branch):
			continue
		bits = _student_bits(student)
		expected = _resolve_student_email(row.custom_school_id, row.student_email_id)
		if not row.user:
			findings.append(_finding(INFO, "Account", _("No login yet"), **bits))
			continue
		if expected and row.user.lower() != expected.lower():
			findings.append(
				_finding(
					REVIEW,
					"Account",
					_("Login {0} does not match the School ID's address {1}").format(row.user, expected),
					**bits,
				)
			)
		user = users.get(row.user)
		if user is not None and not cint(user.enabled):
			findings.append(
				_finding(
					REVIEW,
					"Account",
					_("Student is enabled but their login {0} is disabled").format(row.user),
					**bits,
				)
			)
	return findings


def _exam_checks(ctx, branch):
	findings = []
	if not frappe.db.table_exists("Student Exit"):
		return findings
	graduates = frappe.get_all(
		"Student Exit",
		filters={"docstatus": 1, "exit_type": "Graduated", "national_exam_result": ["is", "not set"]},
		fields=["name", "student", "student_name", "academic_year"],
		limit_page_length=0,
	)
	for row in graduates:
		student = ctx.students.get(row.student)
		if student and not _in_branch(ctx, student, branch):
			continue
		findings.append(
			_finding(
				INFO,
				"Exam",
				_("Graduated ({0}) with no Grade 12 national exam result recorded").format(
					row.academic_year
				),
				reference_doctype="Student Exit",
				reference_name=row.name,
				**(_student_bits(student) if student else {"student": row.student}),
			)
		)

	# Regional exams: only once results for that exam and year have started
	# being entered, otherwise every Grade 6/8 student would be listed.
	for grade, exam_type in (("Grade 6", "Grade 6 Regional Exam"), ("Grade 8", "Grade 8 Regional Exam")):
		if not any(key[1] == exam_type for key in ctx.exam_results):
			continue
		for student_name, rows in ctx.prev_enrollments.items():
			program = rows[0].program
			if not program.startswith(grade + " ") and program != grade:
				continue
			if (student_name, exam_type) in ctx.exam_results:
				continue
			student = ctx.students.get(student_name)
			if not student or not _in_branch(ctx, student, branch):
				continue
			findings.append(
				_finding(
					INFO,
					"Exam",
					_("No {0} result recorded for {1}").format(exam_type, ctx.previous_year),
					previous_program=program,
					**_student_bits(student),
				)
			)
	return findings
