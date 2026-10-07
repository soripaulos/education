# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class PushToken(Document):
    def validate(self):
        """Validate push token before saving"""
        if self.is_active:
            # Deactivate other tokens for the same user and device type
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
            # A device token addresses one physical phone. Whoever signed in on
            # it last owns it; every other account that once used the phone
            # must stop receiving pushes on it, or that phone gets their
            # notifications too.
            release_token_from_other_users(self.push_token, self.user, exclude_name=self.name)

        # Update last used timestamp
        self.last_used = now()


def release_token_from_other_users(push_token, user_id, exclude_name=None):
    """Deactivate every row for `push_token` that belongs to a user other than `user_id`."""
    if not push_token:
        return
    filters = {"push_token": push_token, "user": ("!=", user_id), "is_active": 1}
    if exclude_name:
        filters["name"] = ("!=", exclude_name)
    frappe.db.set_value("Push Token", filters, "is_active", 0)


def claim_push_token(push_token, user_id, device_type="android", app_version=None, device_model=None):
    """Make `user_id` the only active owner of `push_token`.

    The phone a token belongs to may have been used to sign in to many accounts
    (a parent with several children, a staff phone used at registration). Only
    the account signed in last should receive pushes on it, otherwise sending to
    one student notifies the phone of every other student who ever used it.
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

    The same device may be signed in to several accounts over time. Rows are kept
    per user+token for history, but only the most recent user's row stays active.
    """
    if not user_id or user_id != frappe.session.user and "System Manager" not in frappe.get_roles():
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
