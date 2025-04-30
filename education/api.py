@frappe.whitelist()
def get_active_banner():
    """Get the currently active banner for the user"""
    # Check if there's an active site-wide banner
    banners = frappe.get_all(
        "Education Banner",
        filters={
            "active": 1,
            "start_date": ["<=", frappe.utils.nowdate()],
            "end_date": [">=", frappe.utils.nowdate()]
        },
        fields=["name", "banner_type", "title", "message", "icon", 
                "action_text", "action_url", "dismissable", "auto_dismiss"]
    )
    
    if not banners:
        return None
    
    # Check if the user has dismissed this banner
    banner = banners[0]
    dismissed = frappe.db.exists(
        "Banner Dismissal",
        {
            "banner": banner.name,
            "user": frappe.session.user
        }
    )
    
    if dismissed:
        return None
    
    return {
        "id": banner.name,
        "type": banner.banner_type or "info",
        "title": banner.title,
        "message": banner.message,
        "icon": banner.icon or "info",
        "action_text": banner.action_text,
        "action_url": banner.action_url,
        "dismissable": banner.dismissable,
        "auto_dismiss": banner.auto_dismiss or 0
    }

@frappe.whitelist()
def dismiss_banner(banner_id):
    """Mark a banner as dismissed for the current user"""
    if not banner_id:
        return
    
    # Create a dismissal record
    dismissal = frappe.new_doc("Banner Dismissal")
    dismissal.banner = banner_id
    dismissal.user = frappe.session.user
    dismissal.dismissed_on = frappe.utils.now()
    dismissal.insert(ignore_permissions=True)
    
    return {"success": True}

@frappe.whitelist()
def delete_read_notifications():
    """Delete all read notifications for the current user"""
    frappe.db.delete(
        "Student Notification",
        {
            "to_user": frappe.session.user,
            "read": 1
        }
    )
    return {"success": True}

@frappe.whitelist()
def delete_all_notifications():
    """Delete all notifications for the current user"""
    frappe.db.delete(
        "Student Notification",
        {
            "to_user": frappe.session.user
        }
    )
    return {"success": True}

@frappe.whitelist()
def export_notifications():
    """Export notifications as CSV"""
    from frappe.utils.csvutils import to_csv
    
    notifications = frappe.get_all(
        "Student Notification",
        filters={"to_user": frappe.session.user},
        fields=["from_user", "message", "read", "creation", "reference_document_type", "reference_document_name"],
        order_by="creation desc"
    )
    
    # Clean message content from HTML
    for notification in notifications:
        notification.message = frappe.utils.strip_html_tags(notification.message)
    
    # Convert to CSV
    csv_data = to_csv(notifications)
    
    # Set response headers
    frappe.response["type"] = "download"
    frappe.response["content_type"] = "text/csv"
    frappe.response["content_disposition"] = "attachment; filename=notifications.csv"
    frappe.response["filecontent"] = csv_data
    frappe.response["filename"] = "notifications.csv"

@frappe.whitelist()
def register_notification_token(token):
    """Register a device token for push notifications"""
    if not token:
        return {"success": False, "message": "Token is required"}
    
    user = frappe.session.user
    
    try:
        device = frappe.new_doc("Push Notification Device")
        device.user = user
        device.token = token
        device.device_type = frappe.request.headers.get("User-Agent", "Unknown")
        device.last_seen = frappe.utils.now()
        device.is_active = 1
        device.insert(ignore_permissions=True)
        
        return {"success": True}
    except Exception as e:
        if "Token already exists" in str(e):
            # This is fine, the token was updated in the before_insert method
            return {"success": True}
        
        frappe.log_error(f"Failed to register token: {str(e)}", "Push Notification Error")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def unregister_notification_token(token):
    """Unregister a device token for push notifications"""
    if not token:
        return {"success": False, "message": "Token is required"}
    
    user = frappe.session.user
    
    try:
        # Find the device by token and user
        devices = frappe.get_all(
            "Push Notification Device",
            filters={
                "user": user,
                "token": token
            },
            fields=["name"]
        )
        
        if not devices:
            return {"success": False, "message": "Token not found"}
        
        # Mark the device as inactive instead of deleting
        device = frappe.get_doc("Push Notification Device", devices[0].name)
        device.is_active = 0
        device.save(ignore_permissions=True)
        
        return {"success": True}
    except Exception as e:
        frappe.log_error(f"Failed to unregister token: {str(e)}", "Push Notification Error")
        return {"success": False, "message": str(e)}

@frappe.whitelist()
def send_test_notification():
    """Send a test notification to the current user"""
    try:
        from frappe.push_notification import PushNotification
        
        push_notification = PushNotification("education")
        if push_notification.is_enabled():
            user = frappe.session.user
            push_notification.send_notification_to_user(
                user,
                "Test Notification",
                "This is a test notification from the Education Portal.",
                link=f"{frappe.utils.get_url()}/education",
                icon=f"{frappe.utils.get_url()}/assets/education/manifest/favicon-196.png",
            )
            return {"success": True, "message": "Test notification sent"}
        else:
            return {"success": False, "message": "Push notifications are not enabled"}
    except ImportError:
        return {"success": False, "message": "Push notification module not available"}
    except Exception as e:
        frappe.log_error(f"Failed to send test notification: {str(e)}", "Push Notification Error")
        return {"success": False, "message": str(e)} 