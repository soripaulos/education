import frappe
from frappe import _

# Add hello_world function directly 
@frappe.whitelist()
def hello_world_direct():
    frappe.log_error("Hello World API called directly from education/api/__init__.py!", "API Test")
    return "Hello from API (education/api/__init__.py)!"

# Try to import the hello_world function from the outer api.py
try:
    from education.api import hello_world, log_assessment_entry
except ImportError as e:
    frappe.log_error(f"Error importing API functions in api/__init__.py: {str(e)}", "Education API Init") 