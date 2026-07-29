import frappe

from education.education.doctype.student_application_page_settings.student_application_page_settings import (
    get_page_html_override,
)


def get_context(context):
    """Set page context to prevent Jinja2 template conflicts"""
    context.title = "Member Registration 1825"
    context.description = "Member registration application form"

    # Optional Desk-managed version of this page. Empty string means "use the
    # deployed template below", which is the normal case. It is rendered through
    # Jinja with the page context so it behaves exactly like the file; Vue's
    # {{ }} bindings survive because Frappe's Jinja preserves undefined
    # expressions.
    override = get_page_html_override("mbreg1825")
    if override:
        try:
            override = frappe.render_template(override, dict(context))
        except Exception:
            frappe.log_error(frappe.get_traceback(), "mbreg1825 Desk override render failed")
            override = ""
    context.html_override = override

    return context