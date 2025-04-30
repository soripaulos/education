# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PushNotificationDevice(Document):
    def validate(self):
        """Validate token details"""
        # Truncate token if it's too long (rare edge case)
        if self.token and len(self.token) > 255:
            self.token = self.token[:255]
        
        # Set last seen time if not provided
        if not self.last_seen:
            self.last_seen = frappe.utils.now()
    
    def before_insert(self):
        """Check for existing tokens"""
        # Find existing tokens for this user
        existing_tokens = frappe.get_all(
            "Push Notification Device",
            filters={
                "user": self.user,
                "token": self.token
            },
            fields=["name"]
        )
        
        if existing_tokens:
            # Instead of creating a duplicate, just update the existing one
            existing = frappe.get_doc("Push Notification Device", existing_tokens[0].name)
            existing.last_seen = frappe.utils.now()
            existing.device_type = self.device_type or existing.device_type
            existing.is_active = 1
            existing.save()
            
            # Raise an exception to prevent creating a duplicate
            frappe.throw("Token already exists and has been updated")
            
    @staticmethod
    def get_active_tokens_for_user(user):
        """Get all active tokens for a user"""
        return frappe.get_all(
            "Push Notification Device",
            filters={
                "user": user,
                "is_active": 1
            },
            fields=["token", "device_type"]
        ) 