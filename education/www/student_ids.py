import frappe
from frappe import _

# Serve fresh every time; this is a staff dashboard, not a cacheable page.
no_cache = 1

# Staff roles allowed to view the generated-IDs dashboard. Membership is pure
# data - grant/revoke these roles to change who has access.
ALLOWED_ROLES = {
    "System Manager",
    "Academics User",
    "Education Manager",
    "DD Student Registrar",
    "Accounts Manager",
    "Accounts User",
}


def get_context(context):
    """Context for the "Generated Student IDs" staff dashboard.

    Login required and restricted to the staff roles above.
    """
    if frappe.session.user == "Guest":
        redirect_to = "/student-ids"
        try:
            if getattr(frappe.local, "request", None) and frappe.local.request.path:
                redirect_to = frappe.local.request.path
        except Exception:
            pass
        frappe.local.flags.redirect_location = "/login?redirect-to=" + redirect_to
        raise frappe.Redirect

    if frappe.session.user != "Administrator" and not (ALLOWED_ROLES & set(frappe.get_roles())):
        frappe.throw(
            _("You are not permitted to view the Generated Student IDs page."),
            frappe.PermissionError,
        )

    context.no_cache = 1
    context.title = "Generated Student IDs"
    context.description = "Applicants and their generated School IDs"
    return context
