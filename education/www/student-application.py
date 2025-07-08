import frappe

def get_context(context):
    # This makes the page accessible without login
    context.no_cache = 1
    context.show_sidebar = False
    
    # Set page title and meta
    context.title = "Student Application"
    context.description = "Apply for admission to our school"
    
    # Add any additional context data if needed
    context.base_url = frappe.utils.get_url()
    
    return context 