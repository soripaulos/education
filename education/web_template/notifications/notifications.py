import frappe

def get_context(context):
    """Add notifications to context for rendering in the template."""
    if frappe.session.user == 'Guest':
        frappe.local.flags.redirect_location = '/login'
        raise frappe.Redirect
        
    context.notifications = frappe.get_all(
        "PWA Notification",
        filters={
            "to_user": frappe.session.user
        },
        fields=["name", "message", "read", "creation", "reference_document_type", "reference_document_name", "from_user"],
        order_by="creation desc"
    )
    
    # Add breadcrumbs
    context.parents = [
        {"name": "Home", "route": "/" }
    ]
    
    return context 