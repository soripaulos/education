# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PushToken(Document):
	def validate(self):
		"""Validate push token before saving"""
		# Deactivate other tokens for the same user and device type
		if self.is_active:
			frappe.db.sql("""
				UPDATE `tabPush Token` 
				SET is_active = 0 
				WHERE user = %s AND device_type = %s AND name != %s
			""", (self.user, self.device_type, self.name or ""))
	
	def before_save(self):
		"""Update last used timestamp"""
		self.last_used = frappe.utils.now()
	
	@staticmethod
	def register_token(user, push_token, device_type, student=None, app_version=None, device_model=None):
		"""Register or update a push token for a user"""
		# Check if token already exists
		existing = frappe.db.exists("Push Token", {"push_token": push_token})
		
		if existing:
			# Update existing token
			doc = frappe.get_doc("Push Token", existing)
			doc.user = user
			doc.student = student
			doc.device_type = device_type
			doc.app_version = app_version
			doc.device_model = device_model
			doc.is_active = 1
			doc.save()
		else:
			# Create new token
			doc = frappe.get_doc({
				"doctype": "Push Token",
				"push_token": push_token,
				"user": user,
				"student": student,
				"device_type": device_type,
				"app_version": app_version,
				"device_model": device_model,
				"is_active": 1
			})
			doc.insert()
		
		return doc
	
	@staticmethod
	def get_active_tokens(users=None, students=None, device_types=None):
		"""Get active push tokens based on filters"""
		conditions = ["is_active = 1"]
		values = []
		
		if users:
			if isinstance(users, str):
				users = [users]
			conditions.append(f"user IN ({','.join(['%s'] * len(users))})")
			values.extend(users)
		
		if students:
			if isinstance(students, str):
				students = [students]
			conditions.append(f"student IN ({','.join(['%s'] * len(students))})")
			values.extend(students)
		
		if device_types:
			if isinstance(device_types, str):
				device_types = [device_types]
			conditions.append(f"device_type IN ({','.join(['%s'] * len(device_types))})")
			values.extend(device_types)
		
		query = f"""
			SELECT push_token, user, student, device_type
			FROM `tabPush Token`
			WHERE {' AND '.join(conditions)}
		"""
		
		return frappe.db.sql(query, values, as_dict=True) 