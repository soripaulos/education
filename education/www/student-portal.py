import frappe
from frappe import _

no_cache = 1

def get_context(context):
    """Set the student portal context"""
    context.no_breadcrumbs = True
    
    # Only allow logged in users
    if not frappe.session.user or frappe.session.user == 'Guest':
        frappe.throw(_("You need to be logged in to access the Student Portal"), frappe.PermissionError)
    
    # Check if the user is a student
    if not frappe.db.exists("Student", {"user": frappe.session.user}):
        frappe.throw(_("You do not have permission to access the Student Portal"), frappe.PermissionError)
    
    return context 