__version__ = "15.5.0"

# Explicitly import and re-export the API functions to make them accessible
try:
    from education.education.api import hello_world, log_assessment_entry, get_assessment_students
except ImportError as e:
    import frappe
    frappe.log_error(f"Error importing API functions: {str(e)}", "Education Module Init")
