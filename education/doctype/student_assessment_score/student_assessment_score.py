# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

ASSESSMENT_MAX_SCORES = {
	"First Test": 15,
	"Second Test": 15,
	"Mid Exam": 20,
	"Final Exam": 50,
}

class StudentAssessmentScore(Document):
	def validate(self):
		self.set_student_name()
		self.set_program()
		self.set_max_score()
		self.validate_student_in_group()
		self.validate_score()

	def set_student_name(self):
		if self.student:
			self.student_name = frappe.db.get_value("Student", self.student, "student_name")

	def set_program(self):
		if self.student_group:
			self.program = frappe.db.get_value("Student Group", self.student_group, "program")
	
	def set_max_score(self):
		if self.assessment_criteria and not self.max_score:
			self.max_score = ASSESSMENT_MAX_SCORES.get(self.assessment_criteria)

	def validate_student_in_group(self):
		if self.student and self.student_group:
			is_in_group = frappe.db.exists(
				"Student Group Student", {"parent": self.student_group, "student": self.student}
			)
			if not is_in_group:
				frappe.throw(
					_("Student {0} does not belong to Student Group {1}").format(
						self.student, self.student_group
					)
				)

	def validate_score(self):
		if self.score is not None and self.max_score is not None:
			if self.score > self.max_score:
				frappe.throw(_("Score cannot be greater than Max Score ({0}) for {1}").format(self.max_score, self.assessment_criteria))
			if self.score < 0:
				frappe.throw(_("Score cannot be negative"))

@frappe.whitelist()
def get_students_for_group(student_group):
	if not student_group:
		frappe.throw(_("Please select a Student Group first"))
	return frappe.get_all(
		"Student Group Student",
		filters={"parent": student_group},
		fields=["student", "student_name"],
		order_by="student_name",
	)

@frappe.whitelist()
def create_and_submit_score(academic_year, academic_term, student_group, course, assessment_criteria, student, score):
	try:
		doc = frappe.new_doc("Student Assessment Score")
		doc.academic_year = academic_year
		doc.academic_term = academic_term
		doc.student_group = student_group
		doc.course = course
		doc.assessment_criteria = assessment_criteria
		doc.student = student
		doc.score = float(score)
		doc.insert(ignore_permissions=True)
		doc.submit()
		return doc
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Student Assessment Score API Error")
		frappe.throw(str(e)) 