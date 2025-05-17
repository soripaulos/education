@frappe.whitelist()
def get_notifications():
    """Get notifications for the current user"""
    notifications = frappe.get_all(
        "PWANotification",
        filters={
            "to_user": frappe.session.user,
            # No project_name filter - get all notifications for this user
        },
        fields=["name", "message", "read", "creation", "reference_document_type", "reference_document_name", "from_user"],
        order_by="creation desc"
    )
    return notifications

@frappe.whitelist()
def mark_notification_as_read(notification_id):
    """Mark a notification as read"""
    notification = frappe.get_doc("PWANotification", notification_id)
    if notification.to_user != frappe.session.user:
        frappe.throw(_("Not authorized"))
    
    notification.read = 1
    notification.save(ignore_permissions=True)
    return True

@frappe.whitelist()
def mark_all_notifications_as_read():
    """Mark all notifications as read for the current user"""
    frappe.db.sql("""
        UPDATE `tabPWANotification`
        SET `read` = 1
        WHERE `to_user` = %s
    """, frappe.session.user)
    return True

@frappe.whitelist()
def are_push_notifications_enabled():
    """Check if push notifications are enabled for the site"""
    return frappe.db.get_single_value("Push Notification Settings", "enable_push_notification_relay") 