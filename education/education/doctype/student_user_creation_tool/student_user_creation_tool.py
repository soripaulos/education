# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Create student logins in bulk, separately from enrollment.

Enrollment no longer creates logins, so it is never held up by Frappe's
hourly cap on new users. This tool lists the students who still need one,
and creates them in a background job with the cap lifted for that job only
(see ``lifecycle.accounts``). The initial password is the family phone
number, and a private CSV of what was set is attached for handing out.
"""

import csv
import io
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now, nowdate
from frappe.utils.background_jobs import is_job_enqueued

from education.education.lifecycle.accounts import (
	ensure_student_user,
	student_login,
	student_phone,
	unthrottled_user_creation,
)
from education.education.lifecycle.common import (
	branch_of_section,
	local_phone_digits,
	normalize_school_id,
)

TOOL = "Student User Creation Tool"
JOB_ID = "student_user_creation_tool::create"


class StudentUserCreationTool(Document):
	@frappe.whitelist()
	def get_students(self):
		frappe.only_for(("Education Manager", "System Manager"))
		students = _candidate_students(self)
		rows = []
		users = _existing_users({s.login for s in students})
		for s in students:
			user = users.get(s.login.lower()) if s.login else None
			if user and user.enabled and s.user == user.name and user.has_password:
				state = _("Has login")
			elif user and s.user != user.name:
				state = _("Login exists, not linked")
			elif user and not user.enabled:
				state = _("Login disabled")
			elif user and not user.has_password:
				state = _("No password")
			else:
				state = _("No login")
			if not cint(self.include_with_login) and state == _("Has login"):
				continue
			rows.append(
				{
					"include": 1,
					"student": s.name,
					"student_name": s.student_name,
					"school_id": s.custom_school_id,
					"login": s.login,
					"password_from": s.phone or _("(no usable phone number)"),
					"state": state,
					"program": s.program,
					"student_group": s.student_group,
				}
			)
		if not rows:
			frappe.msgprint(_("Every matching student already has a working login."))
		return rows

	@frappe.whitelist()
	def create_users(self):
		frappe.only_for(("Education Manager", "System Manager"))
		if is_job_enqueued(JOB_ID):
			frappe.throw(_("Logins are already being created. Wait for that run to finish."))
		students = [row.student for row in self.students if cint(row.include) and row.student]
		if not students:
			frappe.throw(_("No students are ticked."))
		frappe.enqueue(
			create_users_job,
			queue="long",
			timeout=4 * 60 * 60,
			job_id=JOB_ID,
			deduplicate=True,
			students=students,
			set_password=cint(self.set_password),
			overwrite_password=cint(self.overwrite_password) and cint(self.include_with_login),
			user=frappe.session.user,
		)
		return {"queued": len(students)}


def _candidate_students(tool):
	"""Enabled students matching the tool's filters, with login and phone."""
	conditions = ["s.enabled = 1"]
	values = {}
	joins = ""
	section_field = frappe.get_meta("Program Enrollment").has_field("student_group")
	if tool.academic_year or tool.program or tool.student_group:
		joins = "JOIN `tabProgram Enrollment` pe ON pe.student = s.name AND pe.docstatus = 1"
		if tool.academic_year:
			conditions.append("pe.academic_year = %(academic_year)s")
			values["academic_year"] = tool.academic_year
		if tool.program:
			conditions.append("pe.program = %(program)s")
			values["program"] = tool.program
		if tool.student_group:
			if section_field:
				conditions.append(
					"(pe.student_group = %(student_group)s OR s.name IN "
					"(SELECT student FROM `tabStudent Group Student` WHERE parent = %(student_group)s))"
				)
			else:
				conditions.append(
					"s.name IN (SELECT student FROM `tabStudent Group Student` WHERE parent = %(student_group)s)"
				)
			values["student_group"] = tool.student_group
	program_col = "pe.program" if joins else "NULL"
	section_col = "pe.student_group" if joins and section_field else "NULL"
	rows = frappe.db.sql(
		f"""
		SELECT DISTINCT s.name, s.student_name, s.first_name, s.middle_name, s.last_name,
			s.custom_school_id, s.student_email_id, s.user, s.student_mobile_number,
			{program_col} AS program, {section_col} AS student_group
		FROM `tabStudent` s
		{joins}
		WHERE {" AND ".join(conditions)}
		ORDER BY s.student_name
		""",
		values,
		as_dict=True,
	)

	if tool.branch:
		branch_of = _branches({normalize_school_id(r.custom_school_id) for r in rows})
		rows = [
			r
			for r in rows
			if (branch_of.get(normalize_school_id(r.custom_school_id)) or branch_of_section(r.student_group))
			== tool.branch
		]

	for row in rows:
		row.login = student_login(row)
		doc = frappe._dict(row)
		if not local_phone_digits(row.student_mobile_number):
			# Only look at guardians when the student's own number is unusable.
			doc.guardians = frappe.get_all(
				"Student Guardian",
				filters={"parent": row.name, "parenttype": "Student"},
				fields=["guardian"],
				order_by="idx",
			)
		row.phone = student_phone(doc)
	return rows


def _branches(school_ids):
	"""Latest applicant branch per School ID."""
	if not school_ids or not frappe.get_meta("Student Applicant").has_field("branch"):
		return {}
	out = {}
	for row in frappe.db.sql(
		"""
		SELECT sa.custom_school_id, sa.branch
		FROM `tabStudent Applicant` sa
		LEFT JOIN `tabAcademic Year` ay ON ay.name = sa.academic_year
		WHERE IFNULL(sa.branch, '') != ''
		ORDER BY ay.year_start_date ASC
		""",
		as_dict=True,
	):
		sid = normalize_school_id(row.custom_school_id)
		if sid in school_ids:
			out[sid] = row.branch
	return out


def _existing_users(logins):
	logins = [l for l in logins if l]
	if not logins:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT u.name, u.enabled,
			EXISTS(SELECT 1 FROM `__Auth` a WHERE a.doctype = 'User' AND a.name = u.name
				AND a.fieldname = 'password') AS has_password
		FROM `tabUser` u WHERE u.name IN %(logins)s
		""",
		{"logins": tuple(logins)},
		as_dict=True,
	)
	return {r.name.lower(): r for r in rows}


def create_users_job(students, set_password=1, overwrite_password=0, user=None):
	user = user or frappe.session.user
	log = frappe._dict(started_on=now(), created=0, linked=0, unchanged=0, passwords=0, failed=[], notes=[])
	credentials = []
	total = len(students)

	with unthrottled_user_creation():
		for index, name in enumerate(students, 1):
			if index % 10 == 1 or index == total:
				frappe.publish_realtime(
					"student_user_creation_tool", {"progress": [index, total]}, user=user
				)
			try:
				student = frappe.get_doc("Student", name)
				result = ensure_student_user(
					student, set_password=cint(set_password), overwrite_password=cint(overwrite_password)
				)
				frappe.db.commit()
			except Exception as e:
				frappe.db.rollback()
				frappe.log_error(frappe.get_traceback(), f"Student User Creation Tool: {name}")
				log.failed.append({"row": name, "error": str(e)})
				continue

			if result.status == "Failed":
				log.failed.append({"row": name, "name": student.student_name, "error": result.message})
				continue
			if result.status == "Created":
				log.created += 1
			elif result.status == "Linked":
				log.linked += 1
			else:
				log.unchanged += 1
			if result.password:
				log.passwords += 1
			if result.message:
				log.notes.append({"row": name, "name": student.student_name, "note": result.message})
			credentials.append(
				[
					student.custom_school_id,
					student.student_name,
					result.user,
					result.password,
					result.password_rule,
					result.status,
				]
			)

	if credentials:
		log.credentials_file = _attach_credentials(credentials)
	log.finished_on = now()
	frappe.db.set_single_value(TOOL, "last_run_log", json.dumps(log, default=str))
	if log.get("credentials_file"):
		frappe.db.set_single_value(TOOL, "credentials_file", log.credentials_file)
	frappe.db.commit()
	frappe.publish_realtime("student_user_creation_tool_done", log, user=user)


def _attach_credentials(rows):
	"""Write the run's logins/passwords to a private CSV attached to the tool."""
	buffer = io.StringIO()
	writer = csv.writer(buffer)
	writer.writerow(["School ID", "Student Name", "Login", "Initial Password", "Password Rule", "Status"])
	writer.writerows(rows)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"student-logins-{nowdate()}-{frappe.generate_hash(length=6)}.csv",
			"is_private": 1,
			"content": buffer.getvalue(),
			"attached_to_doctype": TOOL,
			"attached_to_name": TOOL,
		}
	)
	file_doc.flags.ignore_permissions = True
	file_doc.insert()
	return file_doc.file_url
