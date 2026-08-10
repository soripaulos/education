import frappe
from frappe import _

from education.education.doctype.student_application_page_settings.student_application_page_settings import (
    apply_page_customisations,
)

# Serve fresh every time; this is a gated, data-entry tool, not a cacheable page.
no_cache = 1


# Only holders of this role may open the page. Membership is pure data:
# grant/revoke this role (Desk > User, or via API) to change who has access -
# no code change needed. Currently: Ermias Tesfaye, Nana Abebe, Sori Paulos.
ALLOWED_ROLE = "DD Student Registrar"


def get_context(context):
    """Context for the MBS Dembi Dollo Student Registration Page.

    Unlike the public /mbreg1825 form, this page is login-only and further
    restricted to holders of the "DD Student Registrar" role.
    """
    # 1) Require login. Redirect guests to the login page and back here.
    if frappe.session.user == "Guest":
        redirect_to = "/apply-dd"
        try:
            if getattr(frappe.local, "request", None) and frappe.local.request.path:
                redirect_to = frappe.local.request.path
        except Exception:
            pass
        frappe.local.flags.redirect_location = "/login?redirect-to=" + redirect_to
        raise frappe.Redirect

    # 2) Restrict to holders of the dedicated registrar role. (Administrator
    #    implicitly has every role, so it always retains access.)
    if ALLOWED_ROLE not in frappe.get_roles():
        frappe.throw(
            _("You are not permitted to access the Student Registration Page."),
            frappe.PermissionError,
        )

    context.no_cache = 1
    context.title = "MBS Dembi Dollo Student Registration Page"
    context.description = "MBS Dembi Dollo student registration form"

    # Resolve a valid Academic Year link value. The DD school IDs use the
    # /19 batch suffix, so prefer "2019 E.C." when it exists; otherwise fall
    # back to the most recent academic year so submission never breaks on a
    # missing link target.
    default_academic_year = None
    for candidate in ("2019 E.C.",):
        if frappe.db.exists("Academic Year", candidate):
            default_academic_year = candidate
            break
    if not default_academic_year:
        # ignore_permissions: this only picks a default field value for the
        # form (not exposed as a browsable list), so it must not depend on
        # the calling user's Academic Year read permission - restricted
        # accounts like the DD Student Registrar role have none.
        recent = frappe.get_all(
            "Academic Year",
            filters={"disabled": 0},
            fields=["name"],
            order_by="year_start_date desc",
            limit=1,
            ignore_permissions=True,
        )
        default_academic_year = recent[0].name if recent else "2018 E.C."

    context.default_academic_year = default_academic_year

    # Desk-managed CSS/JS, an optional context script, and an optional full HTML
    # override. The login + role checks above have already run, so nothing here
    # can bypass access control.
    #
    # An override is rendered through Jinja with the same context the file gets,
    # so a copy of the deployed page keeps working: {{ default_academic_year }}
    # is still substituted, while Vue's {{ }} bindings are left untouched
    # (Frappe's Jinja preserves undefined expressions).
    return apply_page_customisations("apply_dd", context)
