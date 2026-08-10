from education.education.doctype.student_application_page_settings.student_application_page_settings import (
    apply_page_customisations,
)


def get_context(context):
    """Set page context to prevent Jinja2 template conflicts"""
    context.title = "Member Registration 1825"
    context.description = "Member registration application form"

    # Desk-managed CSS/JS, an optional context script, and an optional full
    # HTML override. Normally a no-op, in which case the deployed template
    # below is served unchanged.
    return apply_page_customisations("mbreg1825", context)