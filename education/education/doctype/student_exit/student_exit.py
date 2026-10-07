# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A student leaving the school, for whatever reason, recorded once.

Submitting the exit is what makes it take effect: the Student is disabled
with its leaving details, removed from its active sections, and its login
switched off (see ``lifecycle.exits``). Clearance, certificates and any
transcripts handed out later stay editable after submission, so a graduate
collecting a transcript years on is recorded on the same document.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import formatdate, getdate

from education.education.lifecycle import exits


class StudentExit(Document):
	def validate(self):
		self.fill_from_last_enrollment()
		self.validate_dates()
		self.validate_single_open_exit()
		self.link_national_exam_result()

	def fill_from_last_enrollment(self):
		"""Default the last year/program/section from the latest enrollment."""
		if self.academic_year and self.program:
			return
		enrollments = frappe.db.sql(
			"""
			SELECT pe.name, pe.program, pe.academic_year
			FROM `tabProgram Enrollment` pe
			LEFT JOIN `tabAcademic Year` ay ON ay.name = pe.academic_year
			WHERE pe.student = %(student)s AND pe.docstatus = 1
			  AND (%(year)s = '' OR pe.academic_year = %(year)s)
			ORDER BY ay.year_start_date DESC, pe.creation DESC
			LIMIT 1
			""",
			{"student": self.student, "year": self.academic_year or ""},
			as_dict=True,
		)
		if not enrollments:
			return
		latest = enrollments[0]
		self.academic_year = self.academic_year or latest.academic_year
		self.program = self.program or latest.program
		if not self.student_group:
			section = None
			if frappe.get_meta("Program Enrollment").has_field("student_group"):
				section = frappe.db.get_value("Program Enrollment", latest.name, "student_group")
			if not section:
				section = frappe.db.get_value(
					"Student Group Student",
					{"student": self.student, "parenttype": "Student Group"},
					"parent",
					order_by="active desc, modified desc",
				)
			self.student_group = section

	def validate_dates(self):
		joining_date = frappe.db.get_value("Student", self.student, "joining_date")
		if joining_date and self.exit_date and getdate(self.exit_date) < getdate(joining_date):
			frappe.throw(
				_("Exit Date {0} is before the student's Joining Date {1}.").format(
					formatdate(self.exit_date), formatdate(joining_date)
				)
			)
		if self.leaving_certificate_issued_on and self.exit_date:
			if getdate(self.leaving_certificate_issued_on) < getdate(self.exit_date):
				frappe.msgprint(
					_("The leaving certificate is dated before the exit date."), indicator="orange", alert=True
				)

	def validate_single_open_exit(self):
		others = frappe.get_all(
			"Student Exit",
			filters={
				"student": self.student,
				"docstatus": 1,
				"status": "Exited",
				"name": ["!=", self.name],
			},
			pluck="name",
		)
		if others:
			frappe.throw(
				_("{0} already has an open exit ({1}). Amend that one instead.").format(
					self.student_name or self.student, ", ".join(others)
				)
			)

	def link_national_exam_result(self):
		if self.exit_type != "Graduated" or self.national_exam_result:
			return
		result = frappe.get_all(
			"External Exam Result",
			filters={"student": self.student, "exam_type": "Grade 12 National Exam", "docstatus": 1},
			order_by="academic_year desc, creation desc",
			limit=1,
			pluck="name",
		)
		if result:
			self.national_exam_result = result[0]

	def on_submit(self):
		exits.apply_exit(self)
		frappe.msgprint(
			_("{0} is recorded as having left: the student record is disabled.").format(
				self.student_name or self.student
			),
			alert=True,
		)

	def on_cancel(self):
		if self.status == "Readmitted":
			# The readmission already undid the exit; there is nothing left to revert.
			return
		exits.revert_exit(self)

	def on_update_after_submit(self):
		# Keep the Student's certificate number in step when it is filled in later.
		if self.leaving_certificate_number and self.status == "Exited":
			current = frappe.db.get_value("Student", self.student, "leaving_certificate_number")
			if current != self.leaving_certificate_number:
				frappe.db.set_value(
					"Student", self.student, "leaving_certificate_number", self.leaving_certificate_number
				)


@frappe.whitelist()
def get_exit_defaults(student):
	"""Values the form pre-fills for a new exit of ``student``."""
	frappe.has_permission("Student Exit", "create", throw=True)
	doc = frappe.new_doc("Student Exit")
	doc.student = student
	doc.fill_from_last_enrollment()
	return {
		"academic_year": doc.academic_year,
		"program": doc.program,
		"student_group": doc.student_group,
		"exit_type": "Graduated" if (doc.program or "").startswith("Grade 12") else "",
	}
