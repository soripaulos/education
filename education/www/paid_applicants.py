import frappe
from frappe import _

# Serve fresh every time; this is a staff dashboard, not a cacheable page.
no_cache = 1

# Staff roles allowed to view the paid-applicants dashboard.
ALLOWED_ROLES = {
    "System Manager",
    "Academics User",
    "Education Manager",
    "DD Student Registrar",
    "Accounts Manager",
    "Accounts User",
}


def get_context(context):
    """Context for the "Paid Applicants" staff dashboard.

    Login required and restricted to the staff roles above.
    """
    if frappe.session.user == "Guest":
        redirect_to = "/paid-applicants"
        try:
            if getattr(frappe.local, "request", None) and frappe.local.request.path:
                redirect_to = frappe.local.request.path
        except Exception:
            pass
        frappe.local.flags.redirect_location = "/login?redirect-to=" + redirect_to
        raise frappe.Redirect

    if frappe.session.user != "Administrator" and not (ALLOWED_ROLES & set(frappe.get_roles())):
        frappe.throw(
            _("You are not permitted to view the Paid Applicants page."),
            frappe.PermissionError,
        )

    context.no_cache = 1
    context.title = "Paid Applicants"
    context.description = "Applicants who have applied and paid"
    return context
