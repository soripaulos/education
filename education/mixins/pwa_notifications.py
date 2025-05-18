import frappe

class PWANotificationsMixin:
    """
    Mixin class to add PWA notification capabilities to DocTypes.
    This can be used by various Education doctypes to send notifications
    to students, teachers, or other stakeholders.
    """
    
    def notify_user(self, user_id, message, reference_doctype=None, reference_docname=None, from_user=None):
        """
        Send a notification to a specified user
        
        Args:
            user_id (str): The user to notify
            message (str): The notification message
            reference_doctype (str, optional): Reference DocType
            reference_docname (str, optional): Reference Document Name
            from_user (str, optional): The user sending the notification
        """
        if not reference_doctype:
            reference_doctype = self.doctype
            
        if not reference_docname:
            reference_docname = self.name
            
        if not from_user:
            from_user = frappe.session.user
        
        try:
            notification = frappe.new_doc("PWA Notification")
            notification.to_user = user_id
            notification.from_user = from_user
            notification.message = message
            notification.reference_document_type = reference_doctype
            notification.reference_document_name = reference_docname
            notification.read = 0
            notification.insert(ignore_permissions=True)
            
            return notification.name
        except Exception as e:
            frappe.log_error(f"Failed to create notification: {str(e)}", "PWA Notification Error")
            return None
    
    def notify_status_change(self, user_id, status, from_user=None):
        """
        Notify a user about a status change
        
        Args:
            user_id (str): The user to notify
            status (str): The new status
            from_user (str, optional): The user who changed the status
        """
        message = f"Your {self.doctype} '{self.name}' has been {status}"
        return self.notify_user(user_id, message, from_user=from_user)
        
    def notify_assignment(self, user_id, assigned_to, from_user=None):
        """
        Notify a user about an assignment
        
        Args:
            user_id (str): The user to notify
            assigned_to (str): The user assigned to
            from_user (str, optional): The user who made the assignment
        """
        message = f"You have been assigned to {self.doctype} '{self.name}'"
        return self.notify_user(assigned_to, message, from_user=from_user) 