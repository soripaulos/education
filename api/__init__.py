import frappe
from frappe import _

# Add hello_world function directly 
@frappe.whitelist()
def hello_world_direct():
    frappe.log_error("Hello World API called directly from education/api/__init__.py!", "API Test")
    return "Hello from API (education/api/__init__.py)!"

# Don't import from education.api to avoid circular import
@frappe.whitelist()
def hello_world():
    frappe.log_error("Hello World API called from education/api/__init__.py!", "API Test")
    return "Hello from API (education/api/__init__.py standalone)!"

@frappe.whitelist()
def log_assessment_entry(student, assessment_plan, assessment_criteria, score, comments=""):
    """Logs a single assessment score entry for a student and criterion."""
    # Delegate to the implementation in education.education.api
    from education.education.api import log_assessment_entry as original_log_entry
    return original_log_entry(student, assessment_plan, assessment_criteria, score, comments)

@frappe.whitelist()
def subscribe_to_notifications(token):
    """Subscribes a user (student) to push notifications."""
    if not token:
        frappe.throw(_("FCM Token not provided"))

    try:
        # Assuming the standard Frappe push notification app is installed and configured
        # The user will be the currently logged-in student
        frappe.get_doc({
            "doctype": "Push Notification Subscription",
            "user": frappe.session.user,
            "fcm_token": token,
            "device_name": "Student Portal PWA" # Or get from request if available
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": "Subscribed to notifications successfully"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Push Notification Subscription Failed")
        frappe.throw(_("Failed to subscribe to push notifications: {}").format(str(e)))

@frappe.whitelist()
def unsubscribe_from_notifications(token):
    """Unsubscribes a user (student) from push notifications."""
    if not token:
        frappe.throw(_("FCM Token not provided"))
    try:
        # Assuming the standard Frappe push notification app is installed and configured
        frappe.db.delete("Push Notification Subscription", {"fcm_token": token, "user": frappe.session.user})
        frappe.db.commit()
        return {"status": "success", "message": "Unsubscribed from notifications successfully"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Push Notification Unsubscription Failed")
        frappe.throw(_("Failed to unsubscribe from push notifications: {}").format(str(e))) 