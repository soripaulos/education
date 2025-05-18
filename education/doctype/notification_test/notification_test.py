import frappe
from frappe.model.document import Document

class NotificationTest(Document):
    def on_submit(self):
        """Send a test notification when this document is submitted."""
        try:
            notification = frappe.new_doc("PWA Notification")
            notification.to_user = self.user
            notification.from_user = frappe.session.user
            notification.message = self.message
            notification.reference_document_type = "Notification Test"
            notification.reference_document_name = self.name
            notification.read = 0
            notification.insert(ignore_permissions=True)
            
            frappe.msgprint(f"Notification has been sent to {self.user}")
        except Exception as e:
            frappe.throw(f"Failed to send notification: {str(e)}")
    
    def on_cancel(self):
        """Delete the notification when this document is cancelled."""
        notifications = frappe.get_all(
            "PWA Notification",
            filters={
                "reference_document_type": "Notification Test",
                "reference_document_name": self.name
            },
            pluck="name"
        )
        
        for notification in notifications:
            frappe.delete_doc("PWA Notification", notification, ignore_permissions=True)
            
        frappe.msgprint(f"Deleted {len(notifications)} notifications associated with this test.") 