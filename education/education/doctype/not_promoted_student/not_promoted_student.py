# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class NotPromotedStudent(Document):
	def validate(self):
		# Normalise the school ID so lookups from the application pages match
		# regardless of stray whitespace.
		if self.school_id:
			self.school_id = self.school_id.strip()

		# If a Student is linked but the school ID is empty, backfill it.
		if self.student and not self.school_id:
			self.school_id = frappe.db.get_value("Student", self.student, "custom_school_id")
