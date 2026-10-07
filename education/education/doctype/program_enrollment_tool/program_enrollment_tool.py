# Copyright (c) 2015, Frappe and contributors
# For license information, please see license.txt

"""Enroll a new academic year from its applications.

1. Load Students lines last year's enrollments up against this year's
   applications (``lifecycle.reconcile``). Every row says who the student
   is, which grade they are going into, which section, and anything that
   looks wrong.
2. Process Rows enrolls the rows set to Enroll and records an exit for rows
   set to Record Exit. It runs as a background job, re-checks every row on
   the server rather than trusting the browser's copy, and never creates
   logins - the Student User Creation Tool does that afterwards.
3. Roll Over Student Groups moves each section onto the new year and fills
   it with the students enrolled into it.
"""

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, getdate, now
from frappe.utils.background_jobs import is_job_enqueued

from education.education.lifecycle import exits
from education.education.lifecycle.common import is_final_grade, split_program
from education.education.lifecycle.groups import (
	enrollment_has_section_field,
	ensure_section,
	load_groups,
	resolve_section,
	roll_over_groups,
)
from education.education.lifecycle.reconcile import (
	ALREADY_ENROLLED,
	BLOCKED,
	ENROLL,
	GRADUATING,
	NOT_RETURNING,
	RECORD_EXIT,
	build_rows,
	get_previous_academic_year,
)
from education.education.lifecycle.roster import read_roster

TOOL = "Program Enrollment Tool"
PROCESS_JOB = "program_enrollment_tool::process"
GROUPS_JOB = "program_enrollment_tool::groups"

ROW_FIELDS = (
	"action",
	"status",
	"student_applicant",
	"student",
	"student_name",
	"school_id",
	"branch",
	"applicant_type",
	"paid",
	"gender",
	"student_category",
	"previous_program",
	"previous_section",
	"new_program",
	"new_section",
	"section_source",
	"movement",
	"program_enrollment",
	"issues",
)


class ProgramEnrollmentTool(Document):
	def onload(self):
		# The newest academic year is the one being enrolled into; the
		# "current" year in Education Settings still points at the year that
		# is ending while enrollment happens.
		latest = frappe.get_all("Academic Year", order_by="year_start_date desc", limit=1, pluck="name")
		new_year = latest[0] if latest else None
		self.set_onload(
			"defaults",
			{
				"new_academic_year": new_year,
				"academic_year": get_previous_academic_year(new_year) if new_year else None,
			},
		)

	def validate_years(self):
		if not self.academic_year or not self.new_academic_year:
			frappe.throw(_("Choose both the From and the To academic year."))
		if self.academic_year == self.new_academic_year:
			frappe.throw(_("The From and To academic years must be different."))
		starts = {
			year: frappe.db.get_value("Academic Year", year, "year_start_date")
			for year in (self.academic_year, self.new_academic_year)
		}
		if starts[self.academic_year] and starts[self.new_academic_year]:
			if getdate(starts[self.academic_year]) >= getdate(starts[self.new_academic_year]):
				frappe.throw(_("The From academic year must come before the To academic year."))

	@frappe.whitelist()
	def get_students(self):
		frappe.only_for(("Education Manager", "System Manager"))
		self.validate_years()
		roster = read_roster(self.section_roster) if self.section_roster else None
		rows, summary = build_rows(
			self.academic_year,
			self.new_academic_year,
			program=self.program,
			branch=self.branch,
			roster=roster,
			include_enrolled=cint(self.include_already_enrolled),
			include_not_returning=cint(self.include_not_returning),
		)
		if not rows:
			frappe.msgprint(_("No students match these filters."))
		return {
			"rows": [{field: row.get(field) for field in ROW_FIELDS} for row in rows],
			"summary": summary,
		}

	@frappe.whitelist()
	def enroll_students(self):
		frappe.only_for(("Education Manager", "System Manager"))
		self.validate_years()
		if is_job_enqueued(PROCESS_JOB):
			frappe.throw(_("Rows are already being processed. Wait for that run to finish."))

		requests = [
			{
				"action": row.action,
				"student_applicant": row.student_applicant,
				"student": row.student,
				"new_section": (row.new_section or "").strip(),
			}
			for row in self.students
			if row.action in (ENROLL, RECORD_EXIT)
		]
		if not requests:
			frappe.throw(_("No rows are set to Enroll or Record Exit."))

		frappe.enqueue(
			process_rows,
			queue="long",
			timeout=4 * 60 * 60,
			job_id=PROCESS_JOB,
			deduplicate=True,
			previous_year=self.academic_year,
			new_year=self.new_academic_year,
			requests=requests,
			options={
				"enrollment_date": str(self.enrollment_date) if self.enrollment_date else None,
				"create_missing_sections": cint(self.create_missing_sections),
				"exit_type": self.exit_type_for_not_returning or "Did Not Re-register",
				"exit_date": str(self.exit_date) if self.exit_date else None,
				"disable_logins": cint(self.disable_logins_on_exit),
			},
			user=frappe.session.user,
		)
		return {"queued": len(requests)}

	@frappe.whitelist()
	def sync_groups(self):
		frappe.only_for(("Education Manager", "System Manager"))
		self.validate_years()
		if not enrollment_has_section_field():
			frappe.throw(_("Run bench migrate first: Program Enrollment has no Section field yet."))
		if is_job_enqueued(GROUPS_JOB) or is_job_enqueued(PROCESS_JOB):
			frappe.throw(_("Another enrollment job is running. Wait for it to finish."))
		frappe.enqueue(
			sync_groups_job,
			queue="long",
			timeout=60 * 60,
			job_id=GROUPS_JOB,
			deduplicate=True,
			previous_year=self.academic_year,
			new_year=self.new_academic_year,
			disable_unused=cint(self.disable_unused_groups),
			user=frappe.session.user,
		)
		return {"queued": True}


# ---------------------------------------------------------------------------
# Background jobs
# ---------------------------------------------------------------------------


def _progress(user, done, total, title):
	frappe.publish_realtime(
		"program_enrollment_tool", {"progress": [done, total], "title": title}, user=user
	)


def _finish(user, log):
	log["finished_on"] = now()
	frappe.db.set_single_value(TOOL, "last_run_log", json.dumps(log, default=str))
	frappe.db.commit()
	frappe.publish_realtime("program_enrollment_tool_done", log, user=user)


def process_rows(previous_year, new_year, requests, options, user=None):
	"""Enroll / record exits for the requested rows, one transaction per row."""
	user = user or frappe.session.user
	options = frappe._dict(options)
	requests = [frappe._dict(r) for r in requests]

	try:
		fresh_rows, _summary = build_rows(
			previous_year,
			new_year,
			include_enrolled=True,
			include_not_returning=True,
			applicant_names=[
				r.student_applicant for r in requests if r.action == ENROLL and r.student_applicant
			],
			student_names=[r.student for r in requests if r.action == RECORD_EXIT and r.student],
		)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Program Enrollment Tool: re-check failed")
		_finish(user, {"kind": "process", "failed": [{"row": _("All rows"), "error": str(e)}]})
		return
	by_applicant = {r.student_applicant: r for r in fresh_rows if r.student_applicant}
	leavers = {r.student: r for r in fresh_rows if r.status in (NOT_RETURNING, GRADUATING)}

	enrollment_date = options.enrollment_date or frappe.db.get_value(
		"Academic Year", new_year, "year_start_date"
	)
	exit_date = options.exit_date or frappe.db.get_value(
		"Academic Year", previous_year, "year_end_date"
	)

	log = frappe._dict(
		kind="process",
		started_on=now(),
		previous_year=previous_year,
		new_year=new_year,
		enrolled=0,
		new_students=0,
		readmitted=0,
		exits=0,
		skipped=[],
		failed=[],
		notes=[],
		sections_created=[],
	)

	sections = _prepare_sections(requests, by_applicant, new_year, options, log)

	total = len(requests)
	for index, request in enumerate(requests, 1):
		label = request.student_applicant or request.student
		if index % 10 == 1 or index == total:
			_progress(user, index, total, _("Processing rows"))
		try:
			if request.action == ENROLL:
				row = by_applicant.get(request.student_applicant)
				outcome = _enroll(row, request, sections, new_year, enrollment_date, log)
			else:
				row = leavers.get(request.student)
				outcome = _record_exit(row, request, previous_year, exit_date, options, log)
			if outcome:
				log.skipped.append({"row": label, "name": (row or {}).get("student_name"), "reason": outcome})
			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"Program Enrollment Tool: {label}")
			log.failed.append(
				{"row": label, "name": (row or {}).get("student_name") if row else "", "error": str(e)}
			)

	_finish(user, log)


def _prepare_sections(requests, by_applicant, new_year, options, log):
	"""Resolve each requested section to a group, creating missing ones if allowed.

	Returns {typed section name: group name or None}.
	"""
	groups = load_groups()
	resolved = {}
	for request in requests:
		if request.action != ENROLL:
			continue
		row = by_applicant.get(request.student_applicant)
		section = request.new_section or (row.new_section if row else "")
		if not section or section in resolved:
			continue
		group = resolve_section(section, groups)
		if not group and options.create_missing_sections and row and row.new_program:
			try:
				group, created = ensure_section(section, row.new_program, new_year, row.branch or None)
				if created:
					log.sections_created.append(group)
					groups = load_groups()
				frappe.db.commit()
			except Exception as e:
				frappe.db.rollback()
				log.failed.append({"row": section, "name": _("Section"), "error": str(e)})
				group = None
		resolved[section] = group
	return resolved


def _enroll(row, request, sections, new_year, enrollment_date, log):
	"""Enroll one applicant. Returns a reason string when the row is skipped."""
	if not row:
		return _("The application no longer exists, was rejected, or is for another year")
	if row.status == ALREADY_ENROLLED:
		return _("Already enrolled ({0})").format(row.program_enrollment)
	if row.status == BLOCKED:
		blocked = [i["message"] for i in row.issue_list if i["severity"] == BLOCKED]
		return _("Blocked: {0}").format("; ".join(blocked))

	section_name = request.new_section or row.new_section
	section = sections.get(section_name) if section_name else None

	readmitted = []
	if row.student:
		student = row.student
		readmitted = exits.readmit(student) if _needs_readmission(student) else []
	else:
		student = _create_student(row.student_applicant)
		log.new_students += 1

	enrollment = frappe.new_doc("Program Enrollment")
	enrollment.student = student
	enrollment.student_name = row.student_name
	enrollment.program = row.new_program
	enrollment.academic_year = new_year
	enrollment.enrollment_date = enrollment_date
	enrollment.student_category = row.student_category
	base = split_program(row.new_program)[0]
	if frappe.db.exists("Student Batch Name", base):
		enrollment.student_batch_name = base
	if enrollment_has_section_field():
		enrollment.student_group = section
		enrollment.student_applicant = row.student_applicant
	enrollment.flags.ignore_permissions = True
	enrollment.flags.from_enrollment_tool = True
	enrollment.insert()
	enrollment.submit()

	frappe.db.set_value("Student Applicant", row.student_applicant, "application_status", "Admitted")
	for exit_name in readmitted:
		frappe.db.set_value("Student Exit", exit_name, "readmission_enrollment", enrollment.name)
	if readmitted:
		log.readmitted += 1
	log.enrolled += 1
	if section_name and not section:
		log.notes.append(
			{
				"row": row.student_applicant,
				"name": row.student_name,
				"note": _("Enrolled without a section: {0} does not exist").format(section_name),
			}
		)
	return None


def _needs_readmission(student):
	enabled, leaving = frappe.db.get_value("Student", student, ["enabled", "date_of_leaving"])
	return not cint(enabled) or bool(leaving) or bool(exits.open_exits(student))


def _create_student(applicant):
	"""Create the Student for a new applicant - without a login."""
	from education.education.api import _resolve_student_email

	field_map = {"name": "student_applicant", "image": "image"}
	if frappe.get_meta("Student").has_field("custom_student_category"):
		field_map["student_category"] = "custom_student_category"
	student = get_mapped_doc(
		"Student Applicant",
		applicant,
		{"Student Applicant": {"doctype": "Student", "field_map": field_map}},
		ignore_permissions=True,
	)
	student.student_email_id = _resolve_student_email(
		student.get("custom_school_id"), student.get("student_email_id")
	)
	student.enabled = 1
	student.flags.skip_user_creation = True
	student.flags.ignore_permissions = True
	student.insert()
	return student.name


def _record_exit(row, request, previous_year, exit_date, options, log):
	if not row:
		return _("No longer a leaver: they applied, enrolled, or already have an exit record")
	exit_type = "Graduated" if is_final_grade(row.previous_program) else options.exit_type
	exits.make_exit(
		row.student,
		exit_type,
		exit_date=exit_date,
		academic_year=previous_year,
		program=row.previous_program,
		student_group=row.previous_section or None,
		reason_details=_("Recorded by the Program Enrollment Tool: no application for the next year")
		if exit_type != "Graduated"
		else None,
		disable_user_login=options.disable_logins,
	)
	log.exits += 1
	return None


def sync_groups_job(previous_year, new_year, disable_unused=0, user=None):
	user = user or frappe.session.user
	_progress(user, 0, 1, _("Rolling over sections"))
	try:
		summary = roll_over_groups(previous_year, new_year, disable_unused=cint(disable_unused))
		frappe.db.commit()
		log = dict(summary, kind="groups", previous_year=previous_year, new_year=new_year, failed=[])
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Program Enrollment Tool: group rollover")
		log = {"kind": "groups", "failed": [{"row": _("Rollover"), "error": str(e)}]}
	_progress(user, 1, 1, _("Rolling over sections"))
	_finish(user, log)
