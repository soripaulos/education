import frappe
from frappe import _

def get_context(context):
    # Get common context data
    abbr = frappe.db.get_single_value(
        "Education Settings", "school_college_name_abbreviation"
    )
    logo = frappe.db.get_single_value("Education Settings", "school_college_logo")
    context.abbr = abbr or "Frappe Education"
    context.logo = logo or "/favicon.png"
    
    # Current logged-in student
    context.student = frappe.session.user
    
    # Basic page metadata
    context.title = _("Assessment Logs")
    
    # Assessment data will be loaded via JavaScript API call
    return context 