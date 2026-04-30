# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class FeedbackSettings(Document):
	def validate(self):
		# Validate that the taxonomy JSON is valid
		if self.taxonomy_json:
			try:
				json.loads(self.taxonomy_json)
			except json.JSONDecodeError:
				frappe.throw("Invalid JSON format in Taxonomy JSON field")
	
	def on_update(self):
		# Clear cache when taxonomy is updated so forms get fresh data
		frappe.cache().delete_key("feedback_taxonomy") 