# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document

class SchoolFeedback(Document):
	def validate(self):
		if self.student:
			self.student_name = frappe.db.get_value("Student", self.student, "student_name")
		
		# Set default configuration if not exists
		if not self.feedback_categories_config:
			self.set_default_categories_config()
		
		# Validate category hierarchy
		self.validate_category_hierarchy()
	
	def before_insert(self):
		# Auto-populate student from current user if not set
		if not self.student and frappe.session.user:
			student_record = frappe.db.get_value("Student", {"student_email_id": frappe.session.user}, "name")
			if student_record:
				self.student = student_record
		
		# Set default configuration
		if not self.feedback_categories_config:
			self.set_default_categories_config()
	
	def before_save(self):
		if self.student and not self.student_name:
			self.student_name = frappe.db.get_value("Student", self.student, "student_name")
	
	def set_default_categories_config(self):
		"""Set default categories configuration"""
		default_config = {
			"Academic Issues": {
				"Curriculum": ["Content Difficulty", "Pace Too Fast", "Pace Too Slow", "Missing Topics"],
				"Teaching Methods": ["Unclear Explanations", "Lack of Examples", "No Interactive Activities", "Poor Use of Technology"],
				"Assessment": ["Unfair Grading", "Too Many Tests", "Unclear Instructions", "Late Feedback"]
			},
			"Facility Issues": {
				"Classroom": ["Poor Lighting", "Uncomfortable Seating", "Temperature Issues", "Cleanliness"],
				"Technology": ["Broken Equipment", "Internet Issues", "Software Problems", "Lack of Resources"],
				"Safety": ["Security Concerns", "Emergency Procedures", "Maintenance Issues", "Accessibility"]
			},
			"Administrative Issues": {
				"Communication": ["Poor Information Sharing", "Late Notifications", "Unclear Policies", "Language Barriers"],
				"Scheduling": ["Conflicting Times", "Too Many Classes", "Break Time Issues", "Event Planning"],
				"Documentation": ["Missing Records", "Incorrect Information", "Slow Processing", "Lost Documents"]
			},
			"Other Issues": {}
		}
		self.feedback_categories_config = json.dumps(default_config)
	
	def validate_category_hierarchy(self):
		"""Validate that selected category, subcategory, and specific issue are valid"""
		if not self.category:
			return
		
		# Skip validation for "Other Issues" category
		if self.category == "Other Issues":
			# Clear structured fields for "Other Issues"
			self.subcategory = ""
			self.specific_issue = ""
			return
		
		try:
			config = json.loads(self.feedback_categories_config) if self.feedback_categories_config else {}
		except (json.JSONDecodeError, TypeError):
			frappe.throw("Invalid categories configuration format")
		
		# Validate category
		if self.category not in config:
			frappe.throw(f"Invalid category: {self.category}")
		
		# Validate subcategory
		if self.subcategory:
			if self.subcategory not in config.get(self.category, {}):
				frappe.throw(f"Invalid subcategory '{self.subcategory}' for category '{self.category}'")
		
		# Validate specific issue
		if self.specific_issue and self.subcategory:
			valid_issues = config.get(self.category, {}).get(self.subcategory, [])
			if self.specific_issue not in valid_issues:
				frappe.throw(f"Invalid specific issue '{self.specific_issue}' for subcategory '{self.subcategory}'")

@frappe.whitelist()
def get_feedback_categories():
	"""API method to get feedback categories configuration"""
	# Try to get from the latest School Feedback document or return default
	try:
		latest_doc = frappe.get_last_doc("School Feedback")
		if latest_doc and latest_doc.feedback_categories_config:
			return json.loads(latest_doc.feedback_categories_config)
	except:
		pass
	
	# Return default configuration
	return {
		"Academic Issues": {
			"Curriculum": ["Content Difficulty", "Pace Too Fast", "Pace Too Slow", "Missing Topics"],
			"Teaching Methods": ["Unclear Explanations", "Lack of Examples", "No Interactive Activities", "Poor Use of Technology"],
			"Assessment": ["Unfair Grading", "Too Many Tests", "Unclear Instructions", "Late Feedback"]
		},
		"Facility Issues": {
			"Classroom": ["Poor Lighting", "Uncomfortable Seating", "Temperature Issues", "Cleanliness"],
			"Technology": ["Broken Equipment", "Internet Issues", "Software Problems", "Lack of Resources"],
			"Safety": ["Security Concerns", "Emergency Procedures", "Maintenance Issues", "Accessibility"]
		},
		"Administrative Issues": {
			"Communication": ["Poor Information Sharing", "Late Notifications", "Unclear Policies", "Language Barriers"],
			"Scheduling": ["Conflicting Times", "Too Many Classes", "Break Time Issues", "Event Planning"],
			"Documentation": ["Missing Records", "Incorrect Information", "Slow Processing", "Lost Documents"]
		},
		"Other Issues": {}
	} 
