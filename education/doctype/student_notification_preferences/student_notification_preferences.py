# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StudentNotificationPreferences(Document):
    def validate(self):
        """Validate notification preferences"""
        # Ensure we have a student
        if not self.student:
            frappe.throw("Student is required")
        
        # Get the student's user if any
        student_user = frappe.db.get_value("Student", self.student, "student_email_id")
        if not student_user:
            frappe.msgprint("This student does not have a linked user account. Notifications may not be delivered.")
            
    def on_update(self):
        """Update push notification settings when preferences change"""
        # If push notifications are disabled, mark all devices as inactive
        if not self.push_notifications:
            self.disable_push_devices()
            
    def disable_push_devices(self):
        """Disable all push notification devices for the student"""
        student_user = frappe.db.get_value("Student", self.student, "student_email_id")
        if not student_user:
            return
            
        # Get all devices
        devices = frappe.get_all(
            "Push Notification Device",
            filters={
                "user": student_user,
                "is_active": 1
            },
            fields=["name"]
        )
        
        # Mark each device as inactive
        for device in devices:
            frappe.db.set_value("Push Notification Device", device.name, "is_active", 0)
            
    @staticmethod
    def create_default_preferences(student):
        """Create default notification preferences for a student"""
        if frappe.db.exists("Student Notification Preferences", student):
            return
        
        preferences = frappe.new_doc("Student Notification Preferences")
        preferences.student = student
        preferences.email_notifications = 1
        preferences.push_notifications = 1
        preferences.course_updates = 1
        preferences.assignment_notifications = 1
        preferences.fee_reminders = 1
        preferences.exam_notifications = 1
        preferences.attendance_notifications = 1
        preferences.insert(ignore_permissions=True) 