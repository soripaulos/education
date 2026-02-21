import frappe

def get_context(context):
    """Set page context to prevent Jinja2 template conflicts"""
    context.title = "Member Registration 1825"
    context.description = "Member registration application form"
    return context