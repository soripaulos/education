# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, get_datetime
import json
import requests
from typing import List, Dict, Any


class AppNotification(Document):
    def validate(self):
        """Validate the notification before saving"""
        if not self.send_to_all_students and not self.student_groups and not self.students:
            frappe.throw("Please select at least one recipient (Student Groups or Individual Students) or enable 'Send to All Students'")
        
        # Calculate total recipients
        self.calculate_total_recipients()
    
    def calculate_total_recipients(self):
        """Calculate the total number of recipients"""
        total = 0
        unique_students = set()
        
        if self.send_to_all_students:
            # Get all active students
            students = frappe.get_all("Student", filters={"enabled": 1}, pluck="name")
            total = len(students)
        else:
            # Add students from student groups
            for group_row in self.student_groups:
                if group_row.student_group:
                    group_students = frappe.get_all(
                        "Student Group Student",
                        filters={"parent": group_row.student_group, "active": 1},
                        pluck="student"
                    )
                    unique_students.update(group_students)
            
            # Add individual students
            for student_row in self.students:
                if student_row.student:
                    unique_students.add(student_row.student)
            
            total = len(unique_students)
        
        self.total_recipients = total
    
    def on_submit(self):
        """Send push notifications when the document is submitted"""
        self.send_push_notifications()
    
    def send_push_notifications(self):
        """Send push notifications to selected recipients"""
        try:
            # Get all recipient push tokens
            push_tokens = self.get_recipient_push_tokens()
            
            if not push_tokens:
                self.status = "Failed"
                self.delivery_status = "No push tokens found for recipients"
                self.save()
                return
            
            # Prepare notification data
            notification_data = self.prepare_notification_data()
            
            # Send notifications
            success_count, error_count, errors = self.send_bulk_notifications(push_tokens, notification_data)
            
            # Update status
            if error_count == 0:
                self.status = "Sent"
                self.delivery_status = f"Successfully sent to {success_count} recipients"
            elif success_count > 0:
                self.status = "Sent"
                self.delivery_status = f"Partially sent: {success_count} successful, {error_count} failed"
            else:
                self.status = "Failed"
                self.delivery_status = f"Failed to send to all {error_count} recipients"
            
            if errors:
                self.error_log = "\n".join(errors)
            
            self.sent_date = now()
            self.save()
            
        except Exception as e:
            frappe.log_error(f"App Notification Error: {str(e)}", "Push Notification Failed")
            self.status = "Failed"
            self.delivery_status = f"Error: {str(e)}"
            self.error_log = str(e)
            self.save()
    
    def get_recipient_push_tokens(self) -> List[Dict[str, str]]:
        """Get push tokens for all recipients"""
        recipient_students = set()
        
        if self.send_to_all_students:
            # Get all active students
            students = frappe.get_all("Student", filters={"enabled": 1}, pluck="name")
            recipient_students.update(students)
        else:
            # Add students from student groups
            for group_row in self.student_groups:
                if group_row.student_group:
                    group_students = frappe.get_all(
                        "Student Group Student",
                        filters={"parent": group_row.student_group, "active": 1},
                        pluck="student"
                    )
                    recipient_students.update(group_students)
            
            # Add individual students
            for student_row in self.students:
                if student_row.student:
                    recipient_students.add(student_row.student)
        
        # Get push tokens for these students
        push_tokens = []
        if recipient_students:
            # Get user IDs for students
            student_users = frappe.get_all(
                "Student",
                filters={"name": ("in", list(recipient_students)), "enabled": 1},
                fields=["name", "user"]
            )
            
            user_ids = [s.user for s in student_users if s.user]
            
            if user_ids:
                # Check if Push Token doctype exists (you may need to create this)
                if frappe.db.exists("DocType", "Push Token"):
                    tokens = frappe.get_all(
                        "Push Token",
                        filters={"user": ("in", user_ids), "is_active": 1},
                        fields=["push_token", "user", "device_type"]
                    )
                    push_tokens.extend([{
                        "token": t.push_token,
                        "user": t.user,
                        "device_type": t.device_type or "android"
                    } for t in tokens])
        
        return push_tokens
    
    def prepare_notification_data(self) -> Dict[str, Any]:
        """Prepare notification data for sending"""
        # Map category to channel ID for mobile app
        category_channel_map = {
            "General": "default",
            "Academic": "academic", 
            "Announcements": "announcements",
            "Urgent": "urgent",
            "Fees": "fees",
            "Events": "events",
            "Examinations": "academic"
        }
        
        # Map priority to notification priority
        priority_map = {
            "Low": "default",
            "Normal": "default", 
            "High": "high",
            "Urgent": "max"
        }
        
        return {
            "title": self.title,
            "body": self.message,
            "data": {
                "type": self.notification_category.lower(),
                "category": self.notification_category,
                "priority": self.priority,
                "notification_id": self.name,
                "timestamp": get_datetime().isoformat(),
                "screen": self.get_target_screen()
            },
            "channelId": category_channel_map.get(self.notification_category, "default"),
            "priority": priority_map.get(self.priority, "default"),
            "sound": "default"
        }
    
    def get_target_screen(self) -> str:
        """Get target screen based on notification category"""
        screen_map = {
            "Academic": "grades",
            "Announcements": "announcements", 
            "Fees": "fees",
            "Events": "schedule",
            "Examinations": "grades",
            "Urgent": "notifications"
        }
        return screen_map.get(self.notification_category, "home")
    
    def send_bulk_notifications(self, push_tokens: List[Dict], notification_data: Dict) -> tuple:
        """Send notifications to multiple tokens using Expo Push API"""
        success_count = 0
        error_count = 0
        errors = []
        
        # Batch tokens for efficient sending (Expo supports up to 100 tokens per request)
        batch_size = 100
        
        for i in range(0, len(push_tokens), batch_size):
            batch_tokens = push_tokens[i:i + batch_size]
            
            try:
                # Prepare messages for this batch
                messages = []
                for token_info in batch_tokens:
                    message = notification_data.copy()
                    message["to"] = token_info["token"]
                    messages.append(message)
                
                # Send batch request to Expo Push API
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
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle both array and object response formats
                    if isinstance(result.get("data"), list):
                        # Array format: {"data": [{"status": "ok"}, ...]}
                        for ticket in result["data"]:
                            if ticket.get("status") == "ok":
                                success_count += 1
                            else:
                                error_count += 1
                                errors.append(f"Push error: {ticket.get('message', 'Unknown error')}")
                    elif isinstance(result.get("data"), dict):
                        # Object format: {"data": {"status": "ok", "id": "..."}}
                        if result["data"].get("status") == "ok":
                            success_count += len(batch_tokens)
                        else:
                            error_count += len(batch_tokens)
                            errors.append(f"Batch error: {result['data'].get('message', 'Unknown error')}")
                    else:
                        error_count += len(batch_tokens)
                        errors.append(f"Unexpected response format: {result}")
                else:
                    error_count += len(batch_tokens)
                    errors.append(f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                error_count += len(batch_tokens)
                errors.append(f"Batch send error: {str(e)}")
                frappe.log_error(f"Push notification batch error: {str(e)}")
        
        return success_count, error_count, errors


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