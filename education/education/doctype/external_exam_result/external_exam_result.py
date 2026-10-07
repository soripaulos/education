# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Results of exams set outside the school.

Grade 6 and Grade 8 sit regional exams that decide whether they move on;
Grade 12 sits the national exam that closes their time at the school. The
overall total, average and Pass/Fail are written here as the exam board
reports them - the school does not re-decide them. For grades whose
Promotion Rule is decided by an outside exam, this Pass/Fail is what counts.
Grade 12 results can also carry a score per subject, and are linked to the
student's graduation exit.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

GRADE_12 = "Grade 12 National Exam"


class ExternalExamResult(Document):
	def validate(self):
		self.validate_duplicate()
		self.fill_from_enrollment()
		self.calculate()

	def validate_duplicate(self):
		existing = frappe.get_all(
			"External Exam Result",
			filters={
				"student": self.student,
				"exam_type": self.exam_type,
				"academic_year": self.academic_year,
				"docstatus": ["<", 2],
				"name": ["!=", self.name],
			},
			pluck="name",
		)
		if existing:
			frappe.throw(
				_("{0} already has a {1} result for {2}: {3}").format(
					self.student_name or self.student, self.exam_type, self.academic_year, existing[0]
				)
			)

	def fill_from_enrollment(self):
		if self.program and self.student_group:
			return
		fields = ["program"]
		if frappe.get_meta("Program Enrollment").has_field("student_group"):
			fields.append("student_group")
		enrollment = frappe.db.get_value(
			"Program Enrollment",
			{"student": self.student, "academic_year": self.academic_year, "docstatus": 1},
			fields,
			as_dict=True,
		)
		if enrollment:
			self.program = self.program or enrollment.program
			self.student_group = self.student_group or enrollment.get("student_group")

	def calculate(self):
		"""Totals from the subject rows when there are any; otherwise as typed."""
		if self.exam_type != GRADE_12 and self.subjects:
			# Subject rows are only kept for the national exam.
			self.set("subjects", [])

		if self.subjects:
			total = total_max = 0.0
			for row in self.subjects:
				if flt(row.max_score) <= 0:
					row.max_score = 100
				if flt(row.score) < 0 or flt(row.score) > flt(row.max_score):
					frappe.throw(
						_("Row {0}: {1} must be between 0 and {2}.").format(row.idx, row.subject, row.max_score)
					)
				row.percentage = flt(row.score) / flt(row.max_score) * 100
				total += flt(row.score)
				total_max += flt(row.max_score)
			self.total_score = total
			self.total_max_score = total_max

		if flt(self.total_max_score) > 0:
			if flt(self.total_score) > flt(self.total_max_score):
				frappe.throw(_("Total Score cannot be more than Out Of."))
			self.average_percentage = flt(self.total_score) / flt(self.total_max_score) * 100
		if flt(self.average_percentage) < 0 or flt(self.average_percentage) > 100:
			frappe.throw(_("Average must be between 0 and 100."))

	def before_submit(self):
		if self.result_status == "Pending":
			frappe.throw(_("Set the Result (Pass, Fail, Absent or Withheld) before submitting."))

	def on_submit(self):
		if self.exam_type == GRADE_12:
			self.link_to_graduation()

	def link_to_graduation(self):
		exit_name = frappe.db.get_value(
			"Student Exit",
			{
				"student": self.student,
				"exit_type": "Graduated",
				"docstatus": 1,
				"national_exam_result": ["is", "not set"],
			},
		)
		if exit_name:
			frappe.db.set_value("Student Exit", exit_name, "national_exam_result", self.name)

	def on_cancel(self):
		for exit_name in frappe.get_all(
			"Student Exit", filters={"national_exam_result": self.name}, pluck="name"
		):
			frappe.db.set_value("Student Exit", exit_name, "national_exam_result", None)
