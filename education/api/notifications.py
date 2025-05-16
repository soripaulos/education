import frappe
from frappe import _

@frappe.whitelist()
def mark_as_read(notification_name):
    """Mark a notification as read"""
    try:
        notification = frappe.get_doc("PWA Notification", notification_name)
        if notification.to_user != frappe.session.user:
            frappe.throw(_("Not authorized"))
            
        notification.read = 1
        notification.save(ignore_permissions=True)
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(f"Error marking notification as read: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_unread_count():
    """Get count of unread notifications"""
    try:
        count = frappe.db.count(
            "PWA Notification",
            filters={
                "to_user": frappe.session.user,
                "read": 0
            }
        )
        return {"count": count}
    except Exception as e:
        frappe.log_error(f"Error getting unread notification count: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_notifications():
    """Get all notifications for the current user"""
    try:
        notifications = frappe.get_all(
            "PWA Notification",
            fields=["name", "message", "read", "creation", "reference_document_type", "reference_document_name"],
            filters={"to_user": frappe.session.user},
            order_by="creation desc"
        )
        return notifications
    except Exception as e:
        frappe.log_error(f"Error getting notifications: {str(e)}")
        return []

@frappe.whitelist()
def are_push_notifications_enabled():
    """Check if push notifications are enabled for the current user"""
    try:
        enabled = frappe.db.get_value(
            "User",
            frappe.session.user,
            "push_notifications_enabled"
        )
        return {"enabled": bool(enabled)}
    except Exception as e:
        frappe.log_error(f"Error checking push notification status: {str(e)}")
        return {"enabled": False}

@frappe.whitelist()
def enable_push_notifications():
    """Enable push notifications for the current user"""
    try:
        frappe.db.set_value(
            "User",
            frappe.session.user,
            "push_notifications_enabled",
            1
        )
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(f"Error enabling push notifications: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def disable_push_notifications():
    """Disable push notifications for the current user"""
    try:
        frappe.db.set_value(
            "User",
            frappe.session.user,
            "push_notifications_enabled",
            0
        )
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(f"Error disabling push notifications: {str(e)}")
        return {"status": "error", "message": str(e)}

def send_student_notification(student_user, message, reference_doctype=None, reference_document=None):
    """Send a direct push notification to a student user using the existing PWA Notification doctype"""
    notification = frappe.new_doc("PWA Notification")
    notification.to_user = student_user
    notification.from_user = frappe.session.user
    notification.message = message
    
    if reference_doctype and reference_document:
        notification.reference_document_type = reference_doctype
        notification.reference_document_name = reference_document
        
    notification.insert(ignore_permissions=True)

@frappe.whitelist()
def send_student_notification_api(student_user, message, reference_doctype=None, reference_document=None):
    """API endpoint to send student notifications"""
    try:
        send_student_notification(
            student_user=student_user,
            message=message,
            reference_doctype=reference_doctype,
            reference_document=reference_document
        )
        return {"status": "success", "message": "Notification sent successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def mark_all_as_read():
    """Mark all notifications as read for the current user"""
    try:
        frappe.db.set_value(
            "PWA Notification",
            {"to_user": frappe.session.user, "read": 0},
            "read",
            1,
            update_modified=False
        )
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(f"Error marking all notifications as read: {str(e)}")
        return {"status": "error", "message": str(e)} 