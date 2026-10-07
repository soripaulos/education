# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class PushToken(Document):
    def validate(self):
        """Validate push token before saving"""
        # An account may be signed in on several phones (the child's own and a
        # parent's), and each keeps its alerts. Tokens of uninstalled apps are
        # switched off when the push service reports them as unregistered.

        # Update last used timestamp
        self.last_used = now()


def claim_push_token(push_token, user_id, device_type="android", app_version=None, device_model=None):
    """Register `push_token` for `user_id`, keeping it active for other accounts too.

    One phone may be signed in to several accounts (a parent with a login per
    child) and keeps receiving each account's notifications, so each
    user+token pair is its own row.
    """
    existing = frappe.db.exists("Push Token", {"push_token": push_token, "user": user_id})

    if existing:
        doc = frappe.get_doc("Push Token", existing)
        doc.device_type = device_type
        doc.is_active = 1
        doc.app_version = app_version
        doc.device_model = device_model
        doc.last_used = now()
        doc.save(ignore_permissions=True)
    else:
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
        doc.insert(ignore_permissions=True)

    return doc


@frappe.whitelist()
def register_push_token(push_token, user_id=None, device_type="android", app_version=None, device_model=None):
    """Register or update push token for a user.

    The same push_token string may be registered to multiple users simultaneously
    (e.g. a shared device used by parent and student accounts).  Each
    user+token pair is stored as a separate record.
    """
    # Only an admin may register a device for someone else's account.
    if not user_id or (user_id != frappe.session.user and "System Manager" not in frappe.get_roles()):
        user_id = frappe.session.user

    claim_push_token(push_token, user_id, device_type, app_version, device_model)

    return {"status": "success", "message": "Push token registered successfully"}


@frappe.whitelist()
def deactivate_push_token(push_token, user_id=None):
    """Deactivate a push token for the current (or specified) user only."""
    if not user_id:
        user_id = frappe.session.user

    existing = frappe.db.exists("Push Token", {"push_token": push_token, "user": user_id})
    if existing:
        frappe.db.set_value("Push Token", existing, "is_active", 0)
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
