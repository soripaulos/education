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
        
        # Check if token already exists
        existing = frappe.db.get_value("Push Token", {"push_token": push_token}, "name")
        
        if existing:
            # Update existing token
            doc = frappe.get_doc("Push Token", existing)
            doc.user = user_id
            doc.device_type = device_type
            doc.is_active = 1
            doc.app_version = app_version
            doc.device_model = device_model
            doc.last_used = now()
            doc.save(ignore_permissions=True)
        else:
            # Deactivate old tokens for this user and device type
            frappe.db.set_value(
                "Push Token",
                {
                    "user": user_id,
                    "device_type": device_type
                },
                "is_active",
                0
            )
            
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
            doc.insert(ignore_permissions=True)
        
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
    """Get notifications for the current user"""
    try:
        user_id = frappe.session.user
        
        if user_id == "Guest":
            frappe.throw(_("Authentication required"))
        
        # Get student record for current user
        student = frappe.db.get_value("Student", {"user": user_id, "enabled": 1}, "name")
        
        if not student:
            return {
                "status": "success",
                "notifications": [],
                "total": 0
            }
        
        # Get notifications sent to this student
        notifications = []
        
        # Get notifications sent to all students
        all_student_notifications = frappe.get_all(
            "App Notification",
            filters={
                "status": "Sent",
                "send_to_all_students": 1
            },
            fields=["name", "title", "message", "notification_category", "priority", "sent_date"],
            order_by="sent_date desc",
            limit=limit,
            start=offset
        )
        
        notifications.extend(all_student_notifications)
        
        # Get notifications sent to student groups this student belongs to
        student_groups = frappe.get_all(
            "Student Group Student",
            filters={"student": student, "active": 1},
            pluck="parent"
        )
        
        if student_groups:
            group_notifications = frappe.db.sql("""
                SELECT DISTINCT an.name, an.title, an.message, an.notification_category, 
                       an.priority, an.sent_date
                FROM `tabApp Notification` an
                INNER JOIN `tabApp Notification Student Group` ansg ON an.name = ansg.parent
                WHERE an.status = 'Sent' 
                AND an.send_to_all_students = 0
                AND ansg.student_group IN %(groups)s
                ORDER BY an.sent_date DESC
                LIMIT %(limit)s OFFSET %(offset)s
            """, {
                "groups": student_groups,
                "limit": limit,
                "offset": offset
            }, as_dict=True)
            
            notifications.extend(group_notifications)
        
        # Get notifications sent directly to this student
        direct_notifications = frappe.db.sql("""
            SELECT DISTINCT an.name, an.title, an.message, an.notification_category, 
                   an.priority, an.sent_date
            FROM `tabApp Notification` an
            INNER JOIN `tabApp Notification Student` ans ON an.name = ans.parent
            WHERE an.status = 'Sent' 
            AND an.send_to_all_students = 0
            AND ans.student = %(student)s
            ORDER BY an.sent_date DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {
            "student": student,
            "limit": limit,
            "offset": offset
        }, as_dict=True)
        
        notifications.extend(direct_notifications)
        
        # Remove duplicates and sort by date
        unique_notifications = {}
        for notif in notifications:
            unique_notifications[notif['name']] = notif
        
        sorted_notifications = sorted(
            unique_notifications.values(),
            key=lambda x: x['sent_date'],
            reverse=True
        )
        
        # Format notifications for mobile app
        formatted_notifications = []
        for notif in sorted_notifications[:limit]:
            formatted_notifications.append({
                "id": notif['name'],
                "title": notif['title'],
                "message": notif['message'],
                "category": notif['notification_category'],
                "priority": notif['priority'],
                "sent_date": notif['sent_date'].isoformat() if notif['sent_date'] else None,
                "read": False  # You can implement read status tracking if needed
            })
        
        return {
            "status": "success",
            "notifications": formatted_notifications,
            "total": len(unique_notifications)
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