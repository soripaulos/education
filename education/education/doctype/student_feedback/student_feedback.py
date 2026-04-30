# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class StudentFeedback(Document):
	def before_save(self):
		# Auto-populate student name if not set
		if self.student and not self.student_name:
			self.student_name = frappe.db.get_value("Student", self.student, "student_name")

		# Auto-populate student if not set (for mobile app users)
		if not self.student and frappe.session.user != "Administrator":
			student = frappe.get_all("Student", filters={"student_email_id": frappe.session.user}, fields=["name", "student_name"])
			if student:
				self.student = student[0].name
				self.student_name = student[0].student_name

	def validate(self):
		# Validate taxonomy fields against settings
		self.validate_feedback_taxonomy()

	def validate_feedback_taxonomy(self):
		"""Validate that the selected category, subcategory, and issue are valid"""
		try:
			settings = frappe.get_single("Feedback Settings")
			if not settings or not settings.taxonomy_json:
				return  # Skip validation if no taxonomy is configured
			
			taxonomy = json.loads(settings.taxonomy_json)
			
			# Validate category
			if self.category and self.category not in taxonomy:
				frappe.throw(f"Invalid category: {self.category}")
			
			# Skip validation for "Other Issues" category
			if self.category == "Other Issues":
				return
			
			# Validate subcategory
			if self.subcategory:
				if not taxonomy.get(self.category) or self.subcategory not in taxonomy[self.category]:
					frappe.throw(f"Invalid subcategory: {self.subcategory} for category: {self.category}")
			
			# Validate specific issue
			if self.specific_issue and self.subcategory:
				valid_issues = taxonomy.get(self.category, {}).get(self.subcategory, [])
				if isinstance(valid_issues, list) and self.specific_issue not in valid_issues:
					frappe.throw(f"Invalid specific issue: {self.specific_issue} for subcategory: {self.subcategory}")
					
		except json.JSONDecodeError:
			frappe.log_error("Invalid JSON in Feedback Settings taxonomy", "Student Feedback Validation")
		except Exception as e:
			frappe.log_error(f"Error validating feedback taxonomy: {str(e)}", "Student Feedback Validation") 