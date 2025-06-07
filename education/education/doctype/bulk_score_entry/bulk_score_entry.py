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


class BulkScoreEntry(Document):
	def on_submit(self):
		max_score = ASSESSMENT_MAX_SCORES.get(self.assessment_criteria)
		if max_score is None:
			frappe.throw(_("Max score not defined for Assessment Criteria: {0}").format(self.assessment_criteria))

		for student_entry in self.students:
			if student_entry.score is not None:
				if student_entry.score > max_score:
					frappe.throw(_("Score for {0} ({1}) cannot be greater than {2}").format(student_entry.student_name, student_entry.score, max_score))
				if student_entry.score < 0:
					frappe.throw(_("Score for {0} ({1}) cannot be negative").format(student_entry.student_name, student_entry.score))
				
				self.create_student_assessment_score(student_entry, max_score)

	def create_student_assessment_score(self, student_entry, max_score):
		doc = frappe.new_doc("Student Assessment Score")
		doc.academic_year = self.academic_year
		doc.academic_term = self.academic_term
		doc.student_group = self.student_group
		doc.course = self.course
		doc.assessment_criteria = self.assessment_criteria
		doc.max_score = max_score
		doc.student = student_entry.student
		doc.score = student_entry.score
		doc.save(ignore_permissions=True)
		doc.submit()
		frappe.msgprint(_("Created Student Assessment Score for {0}").format(student_entry.student_name))


@frappe.whitelist()
def get_max_score(assessment_criteria):
	return ASSESSMENT_MAX_SCORES.get(assessment_criteria)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_students(doctype, txt, searchfield, start, page_len, filters):
	student_group = filters.get("student_group")
	if not student_group:
		frappe.throw(_("Please select a Student Group first"))

	student_list = frappe.get_all(
		"Student Group Student",
		filters={"parent": student_group},
		fields=["student", "student_name"],
		as_list=1,
	)

	return student_list 