# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now, get_datetime
from frappe import _


@frappe.whitelist()
def register_device_token(push_token, device_type="android", app_version=None, device_model=None):
    """Register push token for the current user"""
    try:
        user_id = frappe.session.user
        
        if user_id == "Guest":
            frappe.throw(_("Authentication required"))
        
        from education.education.doctype.push_token.push_token import claim_push_token

        # One row per user+token: a phone signed in to several accounts keeps
        # receiving each account's notifications.
        claim_push_token(push_token, user_id, device_type, app_version, device_model)
        
        return {
            "status": "success",
            "message": "Push token registered successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Push token registration error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_notifications_for_user(limit=20, offset=0):
    """Older inbox API, kept for app versions that still call it.

    Reads the signed-in student's own inbox (Student Notification).
    """
    from education.api.student_inbox import get_inbox

    try:
        inbox = get_inbox(limit=limit, offset=offset)
        return {
            "status": "success",
            "notifications": [
                {
                    "id": n.name,
                    "inbox_id": n.name,
                    "notification": n.notification,
                    "title": n.title,
                    "message": n.message,
                    "category": n.category,
                    "priority": "Urgent" if n.category == "Urgent" else "Normal",
                    "sent_date": n.sent_on.isoformat() if n.sent_on else None,
                    "read": bool(n.is_read),
                }
                for n in inbox["items"]
            ],
            "total": len(inbox["items"]),
            "unread_count": inbox["unread_count"],
        }
    except frappe.PermissionError:
        return {"status": "success", "notifications": [], "total": 0}
    except Exception as e:
        frappe.log_error(f"Get notifications error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def mark_notification_as_read(notification_id):
    """Mark one of the signed-in student's inbox entries read."""
    from education.api.student_inbox import mark_read

    mark_read([notification_id])
    return {
        "status": "success",
        "message": "Notification marked as read"
    }


@frappe.whitelist()
def get_notification_categories():
    """Get available notification categories"""
    return {
        "status": "success",
        "categories": [
            {"value": "General", "label": "General"},
            {"value": "Academic", "label": "Academic"},
            {"value": "Announcements", "label": "Announcements"},
            {"value": "Urgent", "label": "Urgent"},
            {"value": "Fees", "label": "Fees"},
            {"value": "Events", "label": "Events"},
            {"value": "Examinations", "label": "Examinations"}
        ]
    }


@frappe.whitelist()
def test_push_notification():
    """Send a test push notification to the current user"""
    try:
        user_id = frappe.session.user
        
        if user_id == "Guest":
            frappe.throw(_("Authentication required"))
        
        # Get user's push tokens
        tokens = frappe.get_all(
            "Push Token",
            filters={"user": user_id, "is_active": 1},
            fields=["push_token", "device_type"]
        )
        
        if not tokens:
            return {
                "status": "error",
                "message": "No active push tokens found for your account"
            }
        
        # Send test notification
        import requests
        
        messages = []
        for token in tokens:
            messages.append({
                "to": token.push_token,
                "title": "MBS App Test",
                "body": "This is a test notification from MBS App!",
                "data": {
                    "type": "test",
                    "screen": "notifications",
                    "timestamp": get_datetime().isoformat()
                },
                "sound": "default"
            })
        
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
            return {
                "status": "success",
                "message": f"Test notification sent to {len(tokens)} device(s)"
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to send notification: {response.text}"
            }
            
    except Exception as e:
        frappe.log_error(f"Test notification error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        } 