# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SchoolFeedback(Document):
	def validate(self):
		if self.student:
			self.student_name = frappe.db.get_value("Student", self.student, "student_name")

	def before_insert(self):
		# Auto-populate student from session if not set
		if not self.student and frappe.session.user != "Administrator":
			student = frappe.db.get_value("Student", {"student_email_id": frappe.session.user}, "name")
			if student:
				self.student = student
				self.student_name = frappe.db.get_value("Student", student, "student_name") 