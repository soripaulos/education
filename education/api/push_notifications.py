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
    """Get the notifications addressed to the current user's student record.

    Only notifications sent to everyone, to a group the student is active in,
    or to the student directly are returned.
    """
    try:
        user_id = frappe.session.user

        if user_id == "Guest":
            frappe.throw(_("Authentication required"))

        limit = frappe.utils.cint(limit) or 20
        offset = frappe.utils.cint(offset)

        student = frappe.db.get_value("Student", {"user": user_id, "enabled": 1}, "name")

        if not student:
            return {
                "status": "success",
                "notifications": [],
                "total": 0
            }

        condition = """
            an.docstatus = 1
            AND an.status IN ('Sent', 'Partially Sent')
            AND (
                (an.send_to_all_students = 1
                    AND NOT EXISTS (SELECT 1 FROM `tabApp Notification Student` x WHERE x.parent = an.name)
                    AND NOT EXISTS (SELECT 1 FROM `tabApp Notification Student Group` y WHERE y.parent = an.name))
                OR EXISTS (SELECT 1 FROM `tabApp Notification Student` ans
                    WHERE ans.parent = an.name AND ans.student = %(student)s)
                OR EXISTS (SELECT 1 FROM `tabApp Notification Student Group` ansg
                    INNER JOIN `tabStudent Group Student` sgs ON sgs.parent = ansg.student_group
                    WHERE ansg.parent = an.name AND sgs.student = %(student)s AND sgs.active = 1)
            )
        """
        params = {"student": student, "limit": limit, "offset": offset}

        notifications = frappe.db.sql(f"""
            SELECT an.name, an.title, an.message, an.notification_category, an.sent_date
            FROM `tabApp Notification` an
            WHERE {condition}
            ORDER BY an.sent_date DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, params, as_dict=True)

        total = frappe.db.sql(f"""
            SELECT COUNT(*) FROM `tabApp Notification` an WHERE {condition}
        """, params)[0][0]

        formatted_notifications = []
        for notif in notifications:
            formatted_notifications.append({
                "id": notif['name'],
                "title": notif['title'],
                "message": notif['message'],
                "category": notif['notification_category'],
                "priority": "Urgent" if notif['notification_category'] == "Urgent" else "Normal",
                "sent_date": notif['sent_date'].isoformat() if notif['sent_date'] else None,
                "read": False  # You can implement read status tracking if needed
            })

        return {
            "status": "success",
            "notifications": formatted_notifications,
            "total": total
        }

    except Exception as e:
        frappe.log_error(f"Get notifications error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def mark_notification_as_read(notification_id):
    """Mark a notification as read (placeholder for future implementation)"""
    # You can implement notification read status tracking here
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