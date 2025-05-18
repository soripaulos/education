# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PWANotification(Document):
    def after_insert(self):
        """Send push notification after inserting the document."""
        try:
            self.send_push_notification()
        except Exception as e:
            frappe.log_error(f"Failed to send push notification: {str(e)}", "PWA Notification Error")

    def send_push_notification(self):
        """Send push notification to the user."""
        if not frappe.db.get_single_value("Push Notification Settings", "enable_push_notification_relay"):
            return
            
        from frappe.push_notification import PushNotification
        
        push_notification = PushNotification("education")
        if not push_notification.is_enabled():
            return
            
        notification_data = {
            "message": self.message,
            "reference_document_type": self.reference_document_type,
            "reference_document_name": self.reference_document_name,
            "click_action": self.get_notification_link(),
            "from_user": self.from_user
        }
        
        push_notification.send_notification_to_user(self.to_user, notification_data)
        
    def get_notification_link(self):
        """Generate link to the reference document."""
        if self.reference_document_type and self.reference_document_name:
            return f"/app/{frappe.scrub(self.reference_document_type)}/{self.reference_document_name}"
        return "/app/pwa-notification" 