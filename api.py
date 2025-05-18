import frappe
from frappe.utils import get_fullname

@frappe.whitelist()
def are_push_notifications_enabled():
    return frappe.db.get_single_value("Push Notification Settings", "enable_push_notification_relay")

@frappe.whitelist()
def get_student_notifications_list(limit_start=0, limit_page_length=20):
    user = frappe.session.user
    # Ensure PWANotification doctype exists and has the necessary fields
    # This assumes PWANotification stores the recipient in 'to_user'
    # and has fields like 'message', 'from_user', 'creation', 'read', 
    # 'reference_document_type', 'reference_document_name'
    notifications = frappe.get_list(
        "PWA Notification",
        filters={"to_user": user},
        fields=[
            "name",
            "message",
            "from_user",
            "creation",
            "read",
            "reference_document_type",
            "reference_document_name",
        ],
        order_by="creation desc",
        limit_start=limit_start,
        limit_page_length=limit_page_length,
    )
    for notif in notifications:
        if notif.from_user:
            notif.from_user_fullname = get_fullname(notif.from_user)
    return notifications

@frappe.whitelist()
def get_student_unread_notification_count():
    user = frappe.session.user
    return frappe.db.count(
        "PWA Notification",
        {"to_user": user, "read": 0}
    )

@frappe.whitelist()
def mark_student_notification_as_read(name):
    user = frappe.session.user
    try:
        # Ensure the notification belongs to the user before marking as read
        notification = frappe.get_doc("PWA Notification", name)
        if notification.to_user == user:
            notification.read = 1
            notification.save(ignore_permissions=True)
            frappe.db.commit() # Ensure change is committed
            return {"status": "success", "message": "Notification marked as read"}
        else:
            frappe.throw(frappe._("Not permitted to mark this notification as read"), frappe.PermissionError)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in mark_student_notification_as_read")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def mark_all_student_notifications_as_read():
    user = frappe.session.user
    try:
        frappe.db.set_value(
            "PWA Notification",
            {"to_user": user, "read": 0},
            "read",
            1,
            update_modified=False, # Avoid updating modified timestamp for many docs
        )
        frappe.db.commit() # Ensure changes are committed
        return {"status": "success", "message": "All notifications marked as read"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in mark_all_student_notifications_as_read")
        return {"status": "error", "message": str(e)} 