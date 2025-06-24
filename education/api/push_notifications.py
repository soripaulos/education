# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _


@frappe.whitelist()
def register_push_token(push_token, device_type, student=None, app_version=None, device_model=None):
	"""Register a push token for the current user"""
	try:
		from education.education.doctype.push_token.push_token import PushToken
		
		doc = PushToken.register_token(
			user=frappe.session.user,
			push_token=push_token,
			device_type=device_type,
			student=student,
			app_version=app_version,
			device_model=device_model
		)
		
		return {
			"success": True,
			"message": "Push token registered successfully",
			"token_id": doc.name
		}
	except Exception as e:
		frappe.log_error(f"Push token registration failed: {str(e)}", "Push Token Registration Error")
		return {
			"success": False,
			"message": f"Failed to register push token: {str(e)}"
		}


@frappe.whitelist()
def send_notification_to_students(title, message, students, category="general", priority="normal", 
								   image_url=None, action_url=None, data=None):
	"""Send push notification to specific students"""
	try:
		# Create notification document
		doc = frappe.get_doc({
			"doctype": "Push Notification",
			"title": title,
			"message": message,
			"category": category,
			"priority": priority,
			"target_type": "specific_students",
			"image_url": image_url,
			"action_url": action_url,
			"data": json.dumps(data) if data else None,
			"target_students": [{"student": student} for student in students]
		})
		doc.insert()
		doc.submit()
		
		return {
			"success": True,
			"message": "Notification sent successfully",
			"notification_id": doc.name,
			"sent_count": doc.sent_count,
			"failed_count": doc.failed_count
		}
	except Exception as e:
		frappe.log_error(f"Send notification failed: {str(e)}", "Send Notification Error")
		return {
			"success": False,
			"message": f"Failed to send notification: {str(e)}"
		}


@frappe.whitelist()
def send_notification_to_all_students(title, message, category="general", priority="normal",
									   include_parents=False, include_teachers=False,
									   image_url=None, action_url=None, data=None):
	"""Send push notification to all students"""
	try:
		# Create notification document
		doc = frappe.get_doc({
			"doctype": "Push Notification",
			"title": title,
			"message": message,
			"category": category,
			"priority": priority,
			"target_type": "all_students",
			"include_parents": include_parents,
			"include_teachers": include_teachers,
			"image_url": image_url,
			"action_url": action_url,
			"data": json.dumps(data) if data else None
		})
		doc.insert()
		doc.submit()
		
		return {
			"success": True,
			"message": "Notification sent successfully",
			"notification_id": doc.name,
			"sent_count": doc.sent_count,
			"failed_count": doc.failed_count
		}
	except Exception as e:
		frappe.log_error(f"Send notification failed: {str(e)}", "Send Notification Error")
		return {
			"success": False,
			"message": f"Failed to send notification: {str(e)}"
		}


@frappe.whitelist()
def send_notification_to_student_groups(title, message, student_groups, category="general", 
										 priority="normal", include_parents=False, include_teachers=False,
										 image_url=None, action_url=None, data=None):
	"""Send push notification to specific student groups"""
	try:
		# Create notification document
		doc = frappe.get_doc({
			"doctype": "Push Notification",
			"title": title,
			"message": message,
			"category": category,
			"priority": priority,
			"target_type": "student_groups",
			"include_parents": include_parents,
			"include_teachers": include_teachers,
			"image_url": image_url,
			"action_url": action_url,
			"data": json.dumps(data) if data else None,
			"target_student_groups": [{"student_group": group} for group in student_groups]
		})
		doc.insert()
		doc.submit()
		
		return {
			"success": True,
			"message": "Notification sent successfully",
			"notification_id": doc.name,
			"sent_count": doc.sent_count,
			"failed_count": doc.failed_count
		}
	except Exception as e:
		frappe.log_error(f"Send notification failed: {str(e)}", "Send Notification Error")
		return {
			"success": False,
			"message": f"Failed to send notification: {str(e)}"
		}


@frappe.whitelist()
def get_student_list():
	"""Get list of students for selection"""
	try:
		students = frappe.get_all(
			"Student",
			fields=["name", "title", "student_name", "student_email_id"],
			order_by="student_name"
		)
		return {
			"success": True,
			"students": students
		}
	except Exception as e:
		return {
			"success": False,
			"message": f"Failed to get student list: {str(e)}"
		}


@frappe.whitelist()
def get_student_groups():
	"""Get list of student groups for selection"""
	try:
		groups = frappe.get_all(
			"Student Group",
			fields=["name", "group_name", "academic_year", "academic_term"],
			order_by="group_name"
		)
		return {
			"success": True,
			"student_groups": groups
		}
	except Exception as e:
		return {
			"success": False,
			"message": f"Failed to get student groups: {str(e)}"
		}


@frappe.whitelist()
def get_notification_history(limit=50):
	"""Get notification history"""
	try:
		notifications = frappe.get_all(
			"Push Notification",
			fields=["name", "title", "message", "category", "priority", "status", 
					"sent_count", "failed_count", "sent_at", "created_by"],
			order_by="creation desc",
			limit=limit
		)
		return {
			"success": True,
			"notifications": notifications
		}
	except Exception as e:
		return {
			"success": False,
			"message": f"Failed to get notification history: {str(e)}"
		}


@frappe.whitelist()
def get_notification_stats():
	"""Get push notification statistics"""
	try:
		stats = {
			"total_notifications": frappe.db.count("Push Notification"),
			"sent_today": frappe.db.count("Push Notification", {
				"sent_at": [">=", frappe.utils.today()]
			}),
			"active_tokens": frappe.db.count("Push Token", {"is_active": 1}),
			"total_tokens": frappe.db.count("Push Token")
		}
		
		# Get category breakdown
		category_stats = frappe.db.sql("""
			SELECT category, COUNT(*) as count
			FROM `tabPush Notification`
			WHERE status = 'sent'
			GROUP BY category
		""", as_dict=True)
		
		stats["category_breakdown"] = {item['category']: item['count'] for item in category_stats}
		
		return {
			"success": True,
			"stats": stats
		}
	except Exception as e:
		return {
			"success": False,
			"message": f"Failed to get notification stats: {str(e)}"
		}


@frappe.whitelist()
def test_notification(title="Test Notification", message="This is a test notification from MBS App"):
	"""Send a test notification to the current user"""
	try:
		from education.education.doctype.push_notification.push_notification import send_test_notification
		result = send_test_notification(title, message)
		return result
	except Exception as e:
		return {
			"success": False,
			"message": f"Test notification failed: {str(e)}"
		} 