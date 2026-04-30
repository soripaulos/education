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