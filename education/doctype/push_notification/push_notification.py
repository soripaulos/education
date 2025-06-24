# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json
from datetime import datetime


class PushNotification(Document):
	def before_save(self):
		"""Set created_by field"""
		if not self.created_by:
			self.created_by = frappe.session.user
	
	def validate(self):
		"""Validate notification before saving"""
		if self.scheduled_time and self.scheduled_time < frappe.utils.now():
			frappe.throw("Scheduled time cannot be in the past")
	
	def on_submit(self):
		"""Send notification when document is submitted"""
		if self.scheduled_time and self.scheduled_time > frappe.utils.now():
			self.status = "scheduled"
			frappe.enqueue(
				'education.education.doctype.push_notification.push_notification.send_scheduled_notification',
				notification_name=self.name,
				at_time=self.scheduled_time
			)
		else:
			self.send_notification()
	
	def send_notification(self):
		"""Send push notification to target audience"""
		try:
			self.status = "sending"
			self.save()
			
			# Get target tokens
			tokens = self.get_target_tokens()
			
			if not tokens:
				frappe.throw("No valid push tokens found for the target audience")
			
			# Send notifications in batches
			batch_size = 100
			sent_count = 0
			failed_count = 0
			
			for i in range(0, len(tokens), batch_size):
				batch = tokens[i:i + batch_size]
				batch_result = self.send_batch_notification(batch)
				sent_count += batch_result.get('sent', 0)
				failed_count += batch_result.get('failed', 0)
			
			# Update statistics
			self.sent_count = sent_count
			self.failed_count = failed_count
			self.delivered_count = sent_count  # Will be updated by delivery receipts
			self.sent_at = frappe.utils.now()
			self.status = "sent" if failed_count == 0 else "partially_sent"
			self.save()
			
			frappe.msgprint(f"Notification sent to {sent_count} devices. {failed_count} failed.")
			
		except Exception as e:
			self.status = "failed"
			self.save()
			frappe.log_error(f"Push notification failed: {str(e)}", "Push Notification Error")
			frappe.throw(f"Failed to send notification: {str(e)}")
	
	def get_target_tokens(self):
		"""Get push tokens based on target type and filters"""
		from education.education.doctype.push_token.push_token import PushToken
		
		users = []
		students = []
		
		# Get target users based on target type
		if self.target_type == "all_students":
			students = frappe.get_all("Student", pluck="name")
		elif self.target_type == "specific_students":
			students = [row.student for row in self.target_students]
		elif self.target_type == "student_groups":
			for group_row in self.target_student_groups:
				group_students = frappe.get_all(
					"Student Group Student",
					filters={"parent": group_row.student_group},
					pluck="student"
				)
				students.extend(group_students)
		elif self.target_type == "specific_users":
			users = [row.user for row in self.target_users]
		
		# Add parents if requested
		if self.include_parents and students:
			parent_users = frappe.get_all(
				"Guardian Student",
				filters={"student": ["in", students]},
				pluck="guardian"
			)
			parent_emails = frappe.get_all(
				"Guardian",
				filters={"name": ["in", parent_users]},
				pluck="email_address"
			)
			# Get user records for parent emails
			for email in parent_emails:
				user = frappe.db.exists("User", {"email": email})
				if user:
					users.append(user)
		
		# Add teachers if requested
		if self.include_teachers:
			teacher_users = frappe.get_all("Instructor", pluck="employee")
			for employee in teacher_users:
				user = frappe.db.get_value("Employee", employee, "user_id")
				if user:
					users.append(user)
		
		# Filter by device type
		device_types = None if self.device_types == "all" else [self.device_types]
		
		# Get active tokens
		tokens = PushToken.get_active_tokens(
			users=users if users else None,
			students=students if students else None,
			device_types=device_types
		)
		
		return tokens
	
	def send_batch_notification(self, tokens):
		"""Send notification to a batch of tokens"""
		expo_tokens = [token['push_token'] for token in tokens if token['push_token'].startswith('ExponentPushToken')]
		
		if not expo_tokens:
			return {'sent': 0, 'failed': len(tokens)}
		
		# Prepare notification payload
		payload = {
			"to": expo_tokens,
			"title": self.title,
			"body": self.message,
			"data": {
				"category": self.category,
				"priority": self.priority,
				"notification_id": self.name,
				"action_url": self.action_url,
				**(json.loads(self.data) if self.data else {})
			},
			"sound": self.sound or "default",
			"channelId": self.category,
		}
		
		if self.image_url:
			payload["image"] = self.image_url
		
		if self.badge_count:
			payload["badge"] = self.badge_count
		
		# Set priority
		if self.priority == "high":
			payload["priority"] = "high"
		elif self.priority == "urgent":
			payload["priority"] = "high"
			payload["ttl"] = 0
		
		try:
			response = requests.post(
				'https://exp.host/--/api/v2/push/send',
				headers={
					'Accept': 'application/json',
					'Accept-encoding': 'gzip, deflate',
					'Content-Type': 'application/json',
				},
				data=json.dumps(payload),
				timeout=30
			)
			
			result = response.json()
			
			# Log results
			sent_count = 0
			failed_count = 0
			
			if isinstance(result.get('data'), list):
				for i, token_result in enumerate(result['data']):
					token_info = tokens[i] if i < len(tokens) else {}
					self.log_delivery_result(token_info, token_result)
					if token_result.get('status') == 'ok':
						sent_count += 1
					else:
						failed_count += 1
			elif isinstance(result.get('data'), dict):
				# Single result format
				if result['data'].get('status') == 'ok':
					sent_count = len(expo_tokens)
				else:
					failed_count = len(expo_tokens)
					for token_info in tokens:
						self.log_delivery_result(token_info, result['data'])
			
			return {'sent': sent_count, 'failed': failed_count}
			
		except Exception as e:
			frappe.log_error(f"Batch notification failed: {str(e)}", "Push Notification Batch Error")
			# Log failure for all tokens in batch
			for token_info in tokens:
				self.log_delivery_result(token_info, {'status': 'error', 'message': str(e)})
			return {'sent': 0, 'failed': len(tokens)}
	
	def log_delivery_result(self, token_info, result):
		"""Log delivery result for a specific token"""
		try:
			log_entry = frappe.get_doc({
				"doctype": "Push Notification Log",
				"notification": self.name,
				"push_token": token_info.get('push_token'),
				"user": token_info.get('user'),
				"student": token_info.get('student'),
				"device_type": token_info.get('device_type'),
				"status": result.get('status', 'unknown'),
				"error_message": result.get('message'),
				"sent_at": frappe.utils.now()
			})
			log_entry.insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Failed to log delivery result: {str(e)}", "Push Notification Log Error")


@frappe.whitelist()
def send_test_notification(title, message, category="general"):
	"""Send a test notification to the current user"""
	from education.education.doctype.push_token.push_token import PushToken
	
	# Get current user's tokens
	tokens = PushToken.get_active_tokens(users=[frappe.session.user])
	
	if not tokens:
		frappe.throw("No push tokens found for your account. Please make sure you're logged in to the mobile app.")
	
	# Create test notification payload
	payload = {
		"to": [token['push_token'] for token in tokens if token['push_token'].startswith('ExponentPushToken')],
		"title": title,
		"body": message,
		"data": {
			"category": category,
			"priority": "normal",
			"test": True
		},
		"sound": "default",
		"channelId": category,
	}
	
	try:
		response = requests.post(
			'https://exp.host/--/api/v2/push/send',
			headers={
				'Accept': 'application/json',
				'Accept-encoding': 'gzip, deflate',
				'Content-Type': 'application/json',
			},
			data=json.dumps(payload),
			timeout=30
		)
		
		result = response.json()
		return {"success": True, "message": "Test notification sent successfully", "result": result}
		
	except Exception as e:
		frappe.log_error(f"Test notification failed: {str(e)}", "Test Notification Error")
		frappe.throw(f"Failed to send test notification: {str(e)}") 