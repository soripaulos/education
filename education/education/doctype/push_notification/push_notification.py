# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json


class PushNotification(Document):
	def on_submit(self):
		"""Send notification when document is submitted"""
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
			
			# Send notification
			self.send_to_expo(tokens)
			
			# Update status
			self.status = "sent"
			self.sent_at = frappe.utils.now()
			self.save()
			
			frappe.msgprint(f"Notification sent to {len(tokens)} devices.")
			
		except Exception as e:
			self.status = "failed"
			self.save()
			frappe.log_error(f"Push notification failed: {str(e)}", "Push Notification Error")
			frappe.throw(f"Failed to send notification: {str(e)}")
	
	def get_target_tokens(self):
		"""Get push tokens based on target type"""
		tokens = []
		
		# Get target users based on target type
		if self.target_type == "all_students":
			# Get all active push tokens
			tokens = frappe.db.sql("""
				SELECT push_token FROM `tabPush Token` 
				WHERE is_active = 1
			""", as_dict=True)
		elif self.target_type == "specific_students":
			# Get tokens for specific students
			student_list = [row.student for row in self.target_students]
			if student_list:
				tokens = frappe.db.sql("""
					SELECT push_token FROM `tabPush Token` 
					WHERE is_active = 1 AND student IN ({})
				""".format(','.join(['%s'] * len(student_list))), student_list, as_dict=True)
		elif self.target_type == "student_groups":
			# Get tokens for student groups
			for group_row in self.target_student_groups:
				group_students = frappe.get_all(
					"Student Group Student",
					filters={"parent": group_row.student_group},
					pluck="student"
				)
				if group_students:
					group_tokens = frappe.db.sql("""
						SELECT push_token FROM `tabPush Token` 
						WHERE is_active = 1 AND student IN ({})
					""".format(','.join(['%s'] * len(group_students))), group_students, as_dict=True)
					tokens.extend(group_tokens)
		
		return [token['push_token'] for token in tokens if token['push_token']]
	
	def send_to_expo(self, tokens):
		"""Send notification to Expo push service"""
		expo_tokens = [token for token in tokens if token.startswith('ExponentPushToken')]
		
		if not expo_tokens:
			frappe.throw("No valid Expo push tokens found")
		
		# Prepare notification payload
		payload = {
			"to": expo_tokens,
			"title": self.title,
			"body": self.message,
			"data": {
				"category": self.category,
				"notification_id": self.name
			},
			"sound": "default",
			"channelId": self.category,
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
			
			if response.status_code != 200:
				frappe.throw(f"Expo API returned status {response.status_code}")
				
		except Exception as e:
			frappe.throw(f"Failed to send to Expo: {str(e)}")


@frappe.whitelist()
def send_test_notification():
	"""Send a test notification to the current user"""
	# Get current user's tokens
	tokens = frappe.db.sql("""
		SELECT push_token FROM `tabPush Token` 
		WHERE is_active = 1 AND user = %s
	""", frappe.session.user, as_dict=True)
	
	if not tokens:
		frappe.throw("No push tokens found for your account. Please make sure you're logged in to the mobile app.")
	
	expo_tokens = [token['push_token'] for token in tokens if token['push_token'].startswith('ExponentPushToken')]
	
	if not expo_tokens:
		frappe.throw("No valid Expo push tokens found for your account.")
	
	# Create test notification payload
	payload = {
		"to": expo_tokens,
		"title": "MBS App Test",
		"body": "This is a test notification from MBS App!",
		"data": {
			"category": "general",
			"test": True
		},
		"sound": "default",
		"channelId": "general",
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