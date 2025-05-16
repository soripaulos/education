import frappe
from frappe import _

@frappe.whitelist()
def get_unread_count():
    """Get count of unread notifications for current user"""
    if not frappe.session.user:
        return {"count": 0}
        
    count = frappe.db.count(
        "PWA Notification",
        filters={
            "to_user": frappe.session.user,
            "read": 0
        }
    )
    return {"count": count}

@frappe.whitelist()
def are_push_notifications_enabled():
    """Check if push notifications are enabled for the site"""
    enabled = bool(frappe.conf.get("push_relay_server_url"))
    return {"enabled": enabled}

@frappe.whitelist()
def mark_all_as_read():
    """Mark all notifications as read for current user"""
    if not frappe.session.user:
        return
        
    frappe.db.set_value(
        "PWA Notification",
        {
            "to_user": frappe.session.user,
            "read": 0
        },
        "read",
        1
    )
    return {"success": True} 