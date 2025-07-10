import frappe

def get_context(context):
    # This makes the page accessible without login
    context.no_cache = 1
    context.show_sidebar = False
    
    # Set page title and meta
    context.title = "Apply for Admission"
    context.description = "Apply for admission to our school"
    
    # Add any additional context data if needed
    context.base_url = frappe.utils.get_url()
    
    # Initialize variables that might be referenced in template to prevent undefined errors
    context.kebele = ''
    context.sub_city = ''
    context.custom_school_id = ''
    context.image = ''
    context.nationality = 'Ethiopian'
    context.city = 'Adama'
    context.state = 'Oromia'
    context.country = 'Ethiopia'
    
    return context 