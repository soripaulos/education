# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class PushToken(Document):
    def validate(self):
        """Validate push token before saving"""
        # Deactivate other tokens for the same user and device type
        if self.is_active:
            frappe.db.set_value(
                "Push Token",
                {
                    "user": self.user,
                    "device_type": self.device_type,
                    "name": ("!=", self.name)
                },
                "is_active",
                0
            )
        
        # Update last used timestamp
        self.last_used = now()


@frappe.whitelist()
def register_push_token(push_token, user_id=None, device_type="android", app_version=None, device_model=None):
    """Register or update push token for a user"""
    if not user_id:
        user_id = frappe.session.user
    
    # Check if token already exists
    existing = frappe.db.exists("Push Token", {"push_token": push_token})
    
    if existing:
        # Update existing token
        doc = frappe.get_doc("Push Token", existing)
        doc.user = user_id
        doc.device_type = device_type
        doc.is_active = 1
        doc.app_version = app_version
        doc.device_model = device_model
        doc.last_used = now()
        doc.save()
    else:
        # Create new token
        doc = frappe.get_doc({
            "doctype": "Push Token",
            "push_token": push_token,
            "user": user_id,
            "device_type": device_type,
            "is_active": 1,
            "app_version": app_version,
            "device_model": device_model,
            "last_used": now(),
            "created_date": now()
        })
        doc.insert()
    
    return {"status": "success", "message": "Push token registered successfully"}


@frappe.whitelist()
def deactivate_push_token(push_token):
    """Deactivate a push token"""
    if frappe.db.exists("Push Token", {"push_token": push_token}):
        frappe.db.set_value("Push Token", {"push_token": push_token}, "is_active", 0)
        return {"status": "success", "message": "Push token deactivated"}
    else:
        return {"status": "error", "message": "Push token not found"}


@frappe.whitelist()
def get_user_push_tokens(user_id=None):
    """Get active push tokens for a user"""
    if not user_id:
        user_id = frappe.session.user
    
    tokens = frappe.get_all(
        "Push Token",
        filters={"user": user_id, "is_active": 1},
        fields=["push_token", "device_type", "app_version", "last_used"]
    )
    
    return tokens 