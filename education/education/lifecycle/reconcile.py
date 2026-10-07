"""Line last year's students up against this year's applications.

The application for the new academic year is the source of truth: it says
whether a student is coming back and which grade they are coming back to
(a student who was not promoted applies for the same grade again). This
module builds one row per person and attaches every problem found along the
way, so the enrollment tool and the diagnostics report see the same thing.

Row statuses
    Ready            - nothing stands in the way; enrolled by default.
    Review           - enrollable, but a person should look first; skipped
                       unless someone switches the row to Enroll.
    Blocked          - must be fixed at the source (usually the application)
                       and reloaded; never enrolled.
    Already Enrolled - has an enrollment for the new year.
    Not Returning    - enrolled last year, no application this year.
    Graduating       - finished Grade 12 last year.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, formatdate

from education.education.lifecycle.common import (
	BLOCKED,
	CONFLICT,
	INFO,
	MOVED_DOWN,
	PROMOTED,
	REPEATING,
	REVIEW,
	SKIPPED,
	UNKNOWN,
	VARIATION,
	branch_of_section,
	classify_movement,
	compare_names,
	format_issues,
	grade_of_section,
	is_final_grade,
	next_program,
	normalize_name,
	normalize_school_id,
	split_program,
	worst_severity,
)
from education.education.lifecycle.groups import (
	enrollment_has_section_field,
	load_groups,
	resolve_section,
	section_key,
)

READY = "Ready"
ALREADY_ENROLLED = "Already Enrolled"
NOT_RETURNING = "Not Returning"
GRADUATING = "Graduating"

ENROLL = "Enroll"
RECORD_EXIT = "Record Exit"
SKIP = "Skip"

REGIONAL_EXAMS = {"Grade 6": "Grade 6 Regional Exam", "Grade 8": "Grade 8 Regional Exam"}


def get_previous_academic_year(academic_year):
	"""The academic year that ends before ``academic_year`` starts."""
	start = frappe.db.get_value("Academic Year", academic_year, "year_start_date")
	if not start:
		return None
	rows = frappe.get_all(
		"Academic Year",
		filters={"year_start_date": ["<", start]},
		order_by="year_start_date desc",
		limit=1,
		pluck="name",
	)
	return rows[0] if rows else None


def get_pass_mark():
	from education.education.lifecycle.setup import get_setting

	return flt(get_setting("promotion_pass_mark")) or 60.0


def _applicant_fields():
	meta = frappe.get_meta("Student Applicant")
	fields = [
		"name",
		"title",
		"custom_school_id",
		"program",
		"applicant_type",
		"paid",
		"application_status",
		"gender",
		"student_category",
		"student_group",
	]
	for optional in ("branch", "suggested_student_section"):
		if meta.has_field(optional):
			fields.append(optional)
	return fields


class Context:
	"""Everything the row rules need, loaded once with a handful of queries."""

	def __init__(self, previous_year, new_year):
		self.previous_year = previous_year
		self.new_year = new_year
		self.pass_mark = get_pass_mark()
		self.programs = set(frappe.get_all("Program", pluck="name"))
		self.groups = load_groups()
		self.group_keys = {section_key(g): g for g in self.groups}
		has_section = enrollment_has_section_field()

		self.applicants = frappe.get_all(
			"Student Applicant",
			filters={"academic_year": new_year, "application_status": ["!=", "Rejected"]},
			fields=_applicant_fields(),
			limit_page_length=0,
		)
		self.applicants_by_sid = {}
		self.applicants_by_name = {}
		for app in self.applicants:
			app.sid = normalize_school_id(app.custom_school_id)
			app.branch = app.get("branch") or ""
			self.applicants_by_sid.setdefault(app.sid, []).append(app)
			self.applicants_by_name.setdefault(normalize_name(app.title), []).append(app)

		self.students = {}
		self.students_by_sid = {}
		self.students_by_name = {}
		self.students_by_applicant = {}
		for st in frappe.get_all(
			"Student",
			fields=[
				"name",
				"custom_school_id",
				"student_name",
				"enabled",
				"restricted",
				"reason_for_restriction",
				"date_of_leaving",
				"gender",
				"student_applicant",
				"student_category",
			],
			limit_page_length=0,
		):
			st.sid = normalize_school_id(st.custom_school_id or st.name)
			self.students[st.name] = st
			self.students_by_sid[st.sid] = st
			self.students_by_name.setdefault(normalize_name(st.student_name), []).append(st)
			if st.student_applicant:
				self.students_by_applicant[st.student_applicant] = st

		pe_fields = ["name", "student", "program", "docstatus"]
		if has_section:
			pe_fields.append("student_group")
		self.prev_enrollments = {}
		for pe in frappe.get_all(
			"Program Enrollment",
			filters={"academic_year": previous_year, "docstatus": 1},
			fields=pe_fields,
			order_by="creation desc",
			limit_page_length=0,
		):
			self.prev_enrollments.setdefault(pe.student, []).append(pe)

		self.new_enrollments = {}
		for pe in frappe.get_all(
			"Program Enrollment",
			filters={"academic_year": new_year, "docstatus": ["<", 2]},
			fields=pe_fields,
			order_by="docstatus desc, creation desc",
			limit_page_length=0,
		):
			self.new_enrollments.setdefault(pe.student, []).append(pe)

		# Most recent submitted enrollment of any year, for students coming
		# back after a break.
		self.last_enrollment = {}
		for row in frappe.db.sql(
			"""
			SELECT pe.student, pe.program, pe.academic_year
			FROM `tabProgram Enrollment` pe
			LEFT JOIN `tabAcademic Year` ay ON ay.name = pe.academic_year
			WHERE pe.docstatus = 1
			ORDER BY ay.year_start_date DESC, pe.creation DESC
			""",
			as_dict=True,
		):
			self.last_enrollment.setdefault(row.student, row)

		self.prev_membership = {}
		for row in frappe.db.sql(
			"""
			SELECT sgs.student, sgs.parent
			FROM `tabStudent Group Student` sgs
			JOIN `tabStudent Group` sg ON sg.name = sgs.parent
			WHERE sgs.parenttype = 'Student Group' AND sg.academic_year = %s
			ORDER BY sgs.active DESC
			""",
			(previous_year,),
			as_dict=True,
		):
			self.prev_membership.setdefault(row.student, row.parent)

		self.not_promoted_by_sid = {}
		self.not_promoted_by_student = {}
		for row in frappe.get_all(
			"Not Promoted Student",
			filters={"academic_year": previous_year},
			fields=["name", "school_id", "student", "current_program", "reason"],
			limit_page_length=0,
		):
			if row.school_id:
				self.not_promoted_by_sid[normalize_school_id(row.school_id)] = row
			if row.student:
				self.not_promoted_by_student[row.student] = row

		self.year_average = {
			row.student: row.year_average
			for row in frappe.get_all(
				"Student Year Report",
				filters={"academic_year": previous_year},
				fields=["student", "year_average"],
				limit_page_length=0,
			)
		}

		self.exam_results = {}
		if frappe.db.table_exists("External Exam Result"):
			for row in frappe.get_all(
				"External Exam Result",
				filters={"academic_year": previous_year, "docstatus": 1},
				fields=["name", "student", "exam_type", "result_status"],
				limit_page_length=0,
			):
				self.exam_results[(row.student, row.exam_type)] = row

		self.open_exits = {}
		if frappe.db.table_exists("Student Exit"):
			for row in frappe.get_all(
				"Student Exit",
				filters={"docstatus": 1, "status": "Exited"},
				fields=["name", "student", "exit_type", "exit_date"],
				order_by="exit_date desc",
				limit_page_length=0,
			):
				self.open_exits.setdefault(row.student, row)

		# Branch each previous-year student was registered under.
		self.previous_branch = {}
		if frappe.get_meta("Student Applicant").has_field("branch"):
			for row in frappe.get_all(
				"Student Applicant",
				filters={"academic_year": previous_year},
				fields=["custom_school_id", "branch"],
				limit_page_length=0,
			):
				if row.branch:
					self.previous_branch[normalize_school_id(row.custom_school_id)] = row.branch

	def previous_section(self, student, enrollment=None):
		if enrollment and enrollment.get("student_group"):
			return enrollment.student_group
		return self.prev_membership.get(student)

	def branch_of(self, student):
		"""Best guess at the branch a student belongs to.

		This year's application is the most current word. Failing that, last
		year's section ("... Branch" sections are the second campus), since
		applications from before the Branch field existed all say "Main".
		"""
		apps = self.applicants_by_sid.get(student.sid)
		if apps and apps[0].branch:
			return apps[0].branch
		enrollments = self.prev_enrollments.get(student.name) or []
		section = self.previous_section(student.name, enrollments[0] if enrollments else None)
		if section:
			group = self.groups.get(section)
			return group.branch if group else branch_of_section(section)
		return self.previous_branch.get(student.sid, "")


def _new_row(**values):
	row = frappe._dict(
		action=SKIP,
		status="",
		student_applicant="",
		student="",
		student_name="",
		school_id="",
		branch="",
		applicant_type="",
		paid=0,
		gender="",
		student_category="",
		previous_program="",
		previous_section="",
		new_program="",
		new_section="",
		section_source="",
		movement="",
		program_enrollment="",
		issues="",
		issue_list=[],
	)
	row.update(values)
	return row


def _issue(row, severity, category, message):
	row.issue_list.append({"severity": severity, "category": category, "message": message})


def _check_identity(ctx, row, app):
	student = ctx.students_by_sid.get(app.sid) if app.sid else None
	if not student and app.name in ctx.students_by_applicant:
		student = ctx.students_by_applicant[app.name]
		_issue(
			row,
			REVIEW,
			"Identity",
			_("Student {0} was created from this application but carries School ID {1}").format(
				student.name, student.custom_school_id
			),
		)

	if not app.sid:
		_issue(row, BLOCKED, "Identity", _("The application has no School ID"))
	elif len(ctx.applicants_by_sid.get(app.sid, [])) > 1:
		others = [a.name for a in ctx.applicants_by_sid[app.sid] if a.name != app.name]
		_issue(
			row,
			BLOCKED,
			"Identity",
			_("School ID {0} has more than one application this year (also {1})").format(
				app.custom_school_id, ", ".join(others)
			),
		)

	if student:
		verdict = compare_names(app.title, student.student_name)
		if verdict == CONFLICT:
			_issue(
				row,
				BLOCKED,
				"Identity",
				_("School ID {0} belongs to {1}, but the application is for {2}").format(
					app.custom_school_id, student.student_name, app.title
				),
			)
		elif verdict == VARIATION:
			_issue(
				row,
				INFO,
				"Identity",
				_("Name spelled differently: application '{0}', student record '{1}'").format(
					app.title, student.student_name
				),
			)
		if app.applicant_type == "New":
			_issue(
				row,
				REVIEW,
				"Identity",
				_("Marked as a New applicant, but Student {0} already has this School ID").format(
					student.name
				),
			)
		if app.gender and student.gender and app.gender != student.gender:
			_issue(
				row,
				INFO,
				"Identity",
				_("Gender differs: application {0}, student record {1}").format(app.gender, student.gender),
			)
		return student

	namesakes = [
		s for s in ctx.students_by_name.get(normalize_name(app.title), []) if s.sid != app.sid
	]
	if namesakes:
		_issue(
			row,
			REVIEW,
			"Identity",
			_("A student with the same name already exists under another School ID: {0}").format(
				", ".join(f"{s.student_name} ({s.name})" for s in namesakes[:3])
			),
		)
	if app.applicant_type == "Existing":
		if app.branch == "MBS Dembi Dollo":
			_issue(
				row,
				INFO,
				"Identity",
				_("Existing Dembi Dollo student with no Student record yet; one will be created"),
			)
		else:
			_issue(
				row,
				REVIEW,
				"Identity",
				_("Marked Existing, but no Student record has this School ID; a new one would be created"),
			)
	return None


def _check_student_status(ctx, row, student):
	exit_row = ctx.open_exits.get(student.name)
	if exit_row:
		_issue(
			row,
			REVIEW,
			"Exit",
			_("Left on {0} ({1}); enrolling readmits them").format(
				formatdate(exit_row.exit_date), exit_row.exit_type
			),
		)
	elif not cint(student.enabled):
		_issue(row, REVIEW, "Exit", _("Student record is disabled; enrolling re-enables it"))
	elif student.date_of_leaving:
		_issue(
			row,
			REVIEW,
			"Exit",
			_("Student record has a leaving date ({0}) but no exit record").format(
				formatdate(student.date_of_leaving)
			),
		)
	if cint(student.restricted):
		_issue(
			row,
			REVIEW,
			"Status",
			_("Restricted: {0}").format(student.reason_for_restriction or _("no reason given")),
		)


def _check_promotion(ctx, row, app, student):
	previous = None
	if student:
		enrollments = ctx.prev_enrollments.get(student.name, [])
		if len(enrollments) > 1:
			_issue(
				row,
				REVIEW,
				"Enrollment",
				_("Enrolled more than once in {0}: {1}").format(
					ctx.previous_year, ", ".join(f"{e.program} ({e.name})" for e in enrollments)
				),
			)
		previous = enrollments[0] if enrollments else None
		if previous:
			row.previous_program = previous.program
			row.previous_section = ctx.previous_section(student.name, previous) or ""
		else:
			last = ctx.last_enrollment.get(student.name)
			if last:
				row.previous_program = last.program
				_issue(
					row,
					REVIEW,
					"Enrollment",
					_("Not enrolled in {0}; last enrolled in {1} ({2}). Returning after a break").format(
						ctx.previous_year, last.program, last.academic_year
					),
				)
			else:
				_issue(row, REVIEW, "Enrollment", _("Student exists but has never been enrolled"))

	movement, stream_note = classify_movement(row.previous_program, app.program, ctx.programs)
	row.movement = movement

	not_promoted = ctx.not_promoted_by_sid.get(app.sid) or (
		student and ctx.not_promoted_by_student.get(student.name)
	)
	if not_promoted:
		repeat = not_promoted.current_program or row.previous_program
		if repeat and app.program != repeat:
			_issue(
				row,
				BLOCKED,
				"Promotion",
				_(
					"On the {0} Not Promoted list (repeats {1}) but applied for {2}. Correct the application, or remove {3} if the student was promoted."
				).format(ctx.previous_year, repeat, app.program, not_promoted.name),
			)
		else:
			_issue(row, INFO, "Promotion", _("Repeating {0} (Not Promoted list)").format(app.program))
	elif movement == REPEATING:
		_issue(
			row,
			REVIEW,
			"Promotion",
			_("Applied to repeat {0}, but is not on the {1} Not Promoted list").format(
				app.program, ctx.previous_year
			),
		)

	if movement == SKIPPED:
		_issue(
			row,
			REVIEW,
			"Promotion",
			_("Moves from {0} to {1}, skipping a grade").format(row.previous_program, app.program),
		)
	elif movement == MOVED_DOWN:
		_issue(
			row,
			REVIEW,
			"Promotion",
			_("Moves down from {0} to {1}").format(row.previous_program, app.program),
		)
	elif movement == UNKNOWN:
		_issue(
			row,
			REVIEW,
			"Promotion",
			_("Cannot compare {0} with {1}").format(row.previous_program, app.program),
		)

	if movement == PROMOTED and student and not not_promoted:
		average = ctx.year_average.get(student.name)
		if average and flt(average) < ctx.pass_mark:
			_issue(
				row,
				INFO,
				"Promotion",
				_("{0} year average {1} is below the pass mark ({2})").format(
					ctx.previous_year, round(flt(average), 1), ctx.pass_mark
				),
			)
		exam_type = REGIONAL_EXAMS.get(split_program(row.previous_program)[0])
		exam = ctx.exam_results.get((student.name, exam_type)) if exam_type else None
		if exam and exam.result_status == "Fail":
			_issue(
				row,
				REVIEW,
				"Promotion",
				_("Failed the {0} ({1}) but applied for {2}").format(exam_type, exam.name, app.program),
			)

	if stream_note:
		_issue(row, INFO, "Promotion", _("Medium/stream changes: {0}").format(stream_note))


def _choose_section(ctx, row, app, roster):
	section, source = None, ""
	roster_value = (roster or {}).get("sections", {}).get(app.sid) if roster else None
	if roster and app.sid in (roster.get("conflicts") or {}):
		_issue(
			row,
			REVIEW,
			"Section",
			_("Listed under more than one section on the roster: {0}").format(
				", ".join(roster["conflicts"][app.sid])
			),
		)

	if roster_value:
		section = resolve_section(roster_value, ctx.groups, ctx.group_keys) or roster_value
		source = "Roster"
		if section not in ctx.groups:
			_issue(
				row,
				INFO,
				"Section",
				_("Section {0} does not exist yet; it will be created").format(roster_value),
			)
	elif app.student_group:
		section, source = app.student_group, "Application"
	else:
		suggested = resolve_section(app.get("suggested_student_section"), ctx.groups, ctx.group_keys)
		if suggested:
			group = ctx.groups[suggested]
			grade = grade_of_section(suggested)
			wrong_grade = grade and app.program and grade != split_program(app.program)[0]
			wrong_branch = app.branch and group.branch and app.branch != group.branch
			if wrong_grade or wrong_branch:
				_issue(
					row,
					INFO,
					"Section",
					_("Suggested section {0} ignored: it is a {1} section at {2}").format(
						suggested, grade or group.program, group.branch
					),
				)
			else:
				section, source = suggested, "Suggested"
		if roster and not roster_value and app.sid not in (roster.get("conflicts") or {}):
			_issue(row, INFO, "Section", _("Not on the uploaded roster"))

	if not section:
		_issue(row, INFO, "Section", _("No section yet; enrolled without one"))
		return

	row.new_section, row.section_source = section, source
	grade = grade_of_section(section)
	if grade and app.program and grade != split_program(app.program)[0]:
		_issue(
			row,
			REVIEW,
			"Section",
			_("Section {0} is a {1} section, but the student is applying for {2}").format(
				section, grade, app.program
			),
		)
	group = ctx.groups.get(section)
	group_branch = group.branch if group else branch_of_section(section)
	if app.branch and group_branch and app.branch != group_branch:
		_issue(
			row,
			REVIEW,
			"Section",
			_("Section {0} belongs to {1}; the student is registered at {2}").format(
				section, group_branch, app.branch
			),
		)
	if group and group.academic_year == ctx.new_year and group.program and group.program != app.program:
		_issue(
			row,
			REVIEW,
			"Section",
			_("Section {0} is set up for {1} in {2}").format(section, group.program, ctx.new_year),
		)


def _check_new_enrollment(ctx, row, app, student):
	enrollments = ctx.new_enrollments.get(student.name, []) if student else []
	if not enrollments:
		return False
	current = enrollments[0]
	row.program_enrollment = current.name
	if current.get("student_group"):
		row.new_section = current.student_group
		row.section_source = "Enrollment"
	if len(enrollments) > 1:
		_issue(
			row,
			BLOCKED,
			"Enrollment",
			_("More than one enrollment in {0}: {1}").format(
				ctx.new_year, ", ".join(e.name for e in enrollments)
			),
		)
	if current.docstatus == 0:
		_issue(
			row,
			REVIEW,
			"Enrollment",
			_("Enrollment {0} is still a draft; submit or delete it").format(current.name),
		)
	if current.program != app.program:
		_issue(
			row,
			REVIEW,
			"Enrollment",
			_("Enrolled in {0} but the application is for {1}").format(current.program, app.program),
		)
	return True


def build_applicant_row(ctx, app, roster=None):
	row = _new_row(
		student_applicant=app.name,
		student_name=app.title,
		school_id=app.custom_school_id,
		branch=app.branch,
		applicant_type=app.applicant_type,
		paid=cint(app.paid),
		gender=app.gender,
		student_category=app.student_category,
		new_program=app.program,
	)
	if not app.program:
		_issue(row, BLOCKED, "Enrollment", _("The application has no Program"))
	elif app.program not in ctx.programs:
		_issue(row, BLOCKED, "Enrollment", _("Program {0} does not exist").format(app.program))

	student = _check_identity(ctx, row, app)
	if student:
		row.student = student.name
		row.student_category = row.student_category or student.student_category
		_check_student_status(ctx, row, student)
	_check_promotion(ctx, row, app, student)

	already = _check_new_enrollment(ctx, row, app, student)
	if not already:
		_choose_section(ctx, row, app, roster)

	_set_status(row, already)
	return row


def _set_status(row, already=False):
	severity = worst_severity(row.issue_list)
	if already or row.status == ALREADY_ENROLLED:
		row.status = ALREADY_ENROLLED
	elif severity == BLOCKED:
		row.status = BLOCKED
	elif severity == REVIEW:
		row.status = REVIEW
	else:
		row.status = READY
	row.action = ENROLL if row.status == READY else SKIP
	row.issues = format_issues(row.issue_list)


def _flag_section_outliers(rows):
	"""Students whose program differs from the rest of their section.

	A section is one grade in one medium. When nearly everyone placed in it
	applied for "Grade 9 AO", the one "Grade 9" application in it means the
	application or the roster has the wrong medium (or grade).
	"""
	by_section = {}
	for row in rows:
		if row.status not in (READY, REVIEW) or not row.new_section or not row.new_program:
			continue
		by_section.setdefault(row.new_section, []).append(row)
	for section, members in by_section.items():
		counts = {}
		for row in members:
			counts[row.new_program] = counts.get(row.new_program, 0) + 1
		program, count = max(counts.items(), key=lambda item: item[1])
		if len(counts) == 1 or len(members) < 5 or count < 0.6 * len(members):
			continue
		for row in members:
			if row.new_program == program:
				continue
			_issue(
				row,
				REVIEW,
				"Section",
				_("Section {0} is otherwise {1} ({2} of {3} students); this application is for {4}").format(
					section, program, count, len(members), row.new_program
				),
			)
			_set_status(row)


def build_leaver_row(ctx, student, enrollment):
	"""A student enrolled last year with no application and no enrollment this year."""
	sid = student.sid
	row = _new_row(
		student=student.name,
		student_name=student.student_name,
		school_id=student.custom_school_id,
		branch=ctx.branch_of(student),
		gender=student.gender,
		previous_program=enrollment.program,
		previous_section=ctx.previous_section(student.name, enrollment) or "",
	)

	namesakes = [
		a for a in ctx.applicants_by_name.get(normalize_name(student.student_name), []) if a.sid != sid
	]
	if namesakes:
		_issue(
			row,
			REVIEW,
			"Identity",
			_("May have applied under another School ID: {0}").format(
				", ".join(f"{a.custom_school_id} ({a.name}, {a.program})" for a in namesakes[:3])
			),
		)
	not_promoted = ctx.not_promoted_by_sid.get(sid) or ctx.not_promoted_by_student.get(student.name)
	if not_promoted:
		_issue(
			row,
			INFO,
			"Promotion",
			_("On the Not Promoted list (repeats {0}) but has not applied").format(
				not_promoted.current_program or enrollment.program
			),
		)
	if not cint(student.enabled):
		_issue(row, INFO, "Exit", _("Student record is already disabled, but has no exit record"))

	if is_final_grade(enrollment.program):
		row.status = GRADUATING
		row.movement = _("Graduating")
		row.action = RECORD_EXIT if worst_severity(row.issue_list) != REVIEW else SKIP
	else:
		row.status = NOT_RETURNING
		row.movement = _("Not returning")
		row.action = SKIP
	row.issues = format_issues(row.issue_list)
	return row


def build_rows(
	previous_year,
	new_year,
	program=None,
	branch=None,
	roster=None,
	include_enrolled=False,
	include_not_returning=True,
	applicant_names=None,
	student_names=None,
	ctx=None,
):
	"""Build the reconciliation rows plus a summary.

	``program`` filters on the program a student is enrolling into (for
	students not returning: the grade they would have moved into, or the one
	they were in). ``applicant_names``/``student_names`` restrict the result
	to specific people, which is how a processing job re-checks the rows it
	was given instead of trusting what the browser sent back.
	"""
	ctx = ctx or Context(previous_year, new_year)
	applicant_names = set(applicant_names or [])
	student_names = set(student_names or [])
	limited = bool(applicant_names or student_names)

	# Every application is checked even when filtering, so section-level
	# checks see whole sections; the filters are applied afterwards.
	rows = []
	for app in ctx.applicants:
		if limited and app.name not in applicant_names:
			continue
		rows.append(build_applicant_row(ctx, app, roster))
	if not limited:
		_flag_section_outliers(rows)
	rows = [
		r
		for r in rows
		if (not program or r.new_program == program) and (not branch or r.branch == branch)
	]

	if include_not_returning:
		applied = set(ctx.applicants_by_sid)
		for student_name, enrollments in ctx.prev_enrollments.items():
			if limited and student_name not in student_names:
				continue
			student = ctx.students.get(student_name)
			if not student or student.sid in applied:
				continue
			if student_name in ctx.new_enrollments or student_name in ctx.open_exits:
				continue
			enrollment = enrollments[0]
			if program and program not in (
				enrollment.program,
				next_program(enrollment.program, ctx.programs),
			):
				continue
			row = build_leaver_row(ctx, student, enrollment)
			if branch and row.branch and row.branch != branch:
				continue
			rows.append(row)

	summary = summarize(rows, roster, ctx)
	if not include_enrolled:
		rows = [r for r in rows if r.status != ALREADY_ENROLLED]
	rows.sort(key=_sort_key)
	return rows, summary


STATUS_ORDER = [BLOCKED, REVIEW, READY, ALREADY_ENROLLED, GRADUATING, NOT_RETURNING]


def _sort_key(row):
	from education.education.lifecycle.common import grade_index

	program = row.new_program or row.previous_program
	return (
		STATUS_ORDER.index(row.status) if row.status in STATUS_ORDER else 99,
		grade_index(program) if grade_index(program) is not None else 99,
		program or "",
		row.new_section or row.previous_section or "",
		(row.student_name or "").lower(),
	)


def summarize(rows, roster, ctx):
	counts = {}
	for row in rows:
		counts[row.status] = counts.get(row.status, 0) + 1
	unpaid_ready = sum(1 for r in rows if r.status == READY and not r.paid)
	summary = frappe._dict(
		counts=counts,
		total=len(rows),
		unpaid_ready=unpaid_ready,
		roster=None,
	)
	if roster:
		applied = set(ctx.applicants_by_sid)
		missing = sorted(sid for sid in roster.get("sections", {}) if sid not in applied)
		summary.roster = frappe._dict(
			rows=roster.get("rows"),
			students=len(roster.get("sections", {})),
			conflicts=len(roster.get("conflicts") or {}),
			without_application=len(missing),
			without_application_sample=[
				"{0} {1} ({2})".format(
					sid, (roster.get("names") or {}).get(sid, ""), roster["sections"][sid]
				).replace("  ", " ")
				for sid in missing[:40]
			],
		)
	return summary
