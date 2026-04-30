# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, get_datetime
import requests
from typing import List, Dict, Any


class AppNotification(Document):
    def validate(self):
        """Validate the notification before saving."""
        if not self.send_to_all_students and not self.student_groups and not self.students:
            frappe.throw("Please select at least one recipient (Student Groups or Individual Students) or enable 'Send to All Students'")

    def on_submit(self):
        """Send push notifications when the document is submitted."""
        self.send_push_notifications()

    def send_push_notifications(self):
        """Send push notifications to selected recipients."""
        try:
            push_tokens = self._get_recipient_push_tokens()

            if not push_tokens:
                self.status = "Failed"
                frappe.msgprint("No active push tokens found for the selected recipients.")
                return

            notification_data = self._prepare_notification_data()
            self._send_bulk_notifications(push_tokens, notification_data)
            
            self.db_set('status', 'Sent')
            self.db_set('sent_date', now())
            frappe.msgprint("Push notifications sent successfully.")

        except Exception as e:
            self.db_set('status', 'Failed')
            frappe.log_error(f"App Notification Error: {str(e)}", "Push Notification Failed")
            frappe.throw(f"Failed to send notifications: {str(e)}")

    def _get_recipient_push_tokens(self) -> List[str]:
        """Get unique push tokens for all recipients."""
        recipient_students = set()

        if self.send_to_all_students:
            students = frappe.get_all("Student", filters={"enabled": 1}, pluck="name")
            recipient_students.update(students)
        else:
            if self.student_groups:
                student_group_list = [group.student_group for group in self.student_groups if group.student_group]
                if student_group_list:
                    group_students = frappe.get_all(
                        "Student Group Student",
                        filters={"parent": ("in", student_group_list), "active": 1},
                        pluck="student"
                    )
                    recipient_students.update(group_students)
            
            if self.students:
                individual_students = [student.student for student in self.students if student.student]
                recipient_students.update(individual_students)
        
        if not recipient_students:
            return []

        student_users = frappe.get_all(
            "Student",
            filters={"name": ("in", list(recipient_students)), "enabled": 1, "user": ("is", "set")},
            pluck="user"
        )

        if not student_users:
            return []
            
        push_tokens = frappe.get_all(
            "Push Token",
            filters={"user": ("in", student_users), "is_active": 1},
            pluck="push_token"
        )
        return list(set(push_tokens))

    def _prepare_notification_data(self) -> Dict[str, Any]:
        """Prepare the payload for the push notification."""
        return {
            "title": self.title,
            "body": self.message,
            "data": {
                "type": self.notification_category.lower(),
                "category": self.notification_category,
                "notification_id": self.name,
                "timestamp": get_datetime().isoformat(),
                "screen": self.get_target_screen()
            },
            "sound": "default"
        }

    def get_target_screen(self) -> str:
        """Determine the target screen based on notification category."""
        screen_map = {
            "Academic": "grades",
            "Announcements": "announcements",
            "Fees": "fees",
            "Events": "schedule",
            "Examinations": "grades",
        }
        return screen_map.get(self.notification_category, "notifications")

    def _send_bulk_notifications(self, push_tokens: List[str], notification_data: Dict):
        """Send notifications to a list of tokens using Expo Push API."""
        messages = []
        for token in push_tokens:
            message = notification_data.copy()
            message["to"] = token
            messages.append(message)

        if not messages:
            return

        try:
            response = requests.post(
                "https://exp.host/--/api/v2/push/send",
                headers={
                    "Accept": "application/json",
                    "Accept-encoding": "gzip, deflate",
                    "Content-Type": "application/json",
                },
                json=messages,
                timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"Expo API request failed: {e}", "Push Notification Failed")
            # We don't throw an error to the user here as the background job will retry
            # For direct sending, we let the main exception handler catch it.
            raise


@frappe.whitelist()
def send_test_notification(notification_name):
    """API method to send a test notification"""
    doc = frappe.get_doc("App Notification", notification_name)
    
    if doc.status == "Sent":
        frappe.throw("This notification has already been sent")
    
    doc.send_push_notifications()
    return {"status": "success", "message": "Test notification sent"}


@frappe.whitelist()
def get_student_count_for_groups(student_groups):
    """Get total student count for selected student groups"""
    if isinstance(student_groups, str):
        student_groups = json.loads(student_groups)
    
    unique_students = set()
    
    for group_name in student_groups:
        if group_name:
            students = frappe.get_all(
                "Student Group Student",
                filters={"parent": group_name, "active": 1},
                pluck="student"
            )
            unique_students.update(students)
    
    return len(unique_students)


@frappe.whitelist()
def get_all_students_count():
    """Get count of all active students"""
    return frappe.db.count("Student", filters={"enabled": 1}) 