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
def send_student_notification(student_user, message, reference_doctype=None, reference_document=None):
    """Send a notification to a student user"""
    try:
        if not frappe.db.exists("User", student_user):
            frappe.throw(_("Student user not found"))
            
        notification = frappe.new_doc("PWA Notification")
        notification.to_user = student_user
        notification.from_user = frappe.session.user
        notification.message = message
        
        if reference_doctype and reference_document:
            notification.reference_document_type = reference_doctype
            notification.reference_document_name = reference_document
            
        notification.insert(ignore_permissions=True)
        return {"status": "success", "message": "Notification sent successfully"}
    except Exception as e:
        frappe.log_error(f"Error sending student notification: {str(e)}")
        return {"status": "error", "message": str(e)} 