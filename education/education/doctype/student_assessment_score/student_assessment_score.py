# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from education.education.doctype.bulk_score_entry.bulk_score_entry import ASSESSMENT_MAX_SCORES


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
		if self.assessment_criteria:
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