import frappe
from frappe import _


ALLOWED_RESULT_USERS = {"wubet", "sori"}


def ensure_result_page_access():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw(
            _("Please log in to access the Student Result Entry page."), frappe.PermissionError
        )

    username = (frappe.db.get_value("User", user, "username") or "").lower()
    email = (user or "").lower()
    allowed = {u.lower() for u in ALLOWED_RESULT_USERS}
    if email not in allowed and username not in allowed and email != "administrator":
        frappe.throw(_("You are not authorized to access this page."), frappe.PermissionError)


def get_context(context):
    ensure_result_page_access()
    context.title = _("Student Result Entry")

    default_academic_year = "2018 E.C."
    semester_options = [
        {"label": "2018 E.C. (First Semester)", "value": "2018 E.C. (First Semester)"},
        {"label": "2018 E.C. (Second Semester)", "value": "2018 E.C. (Second Semester)"},
    ]
    exam_options = [
        {"label": "First Test", "value": "First Test", "max_score": 15},
        {"label": "Second Test", "value": "Second Test", "max_score": 15},
        {"label": "Mid Exam", "value": "Mid Exam", "max_score": 20},
        {"label": "Final Exam", "value": "Final Exam", "max_score": 50},
    ]

    student_groups = frappe.get_all(
        "Student Group",
        fields=["name", "student_group_name", "program"],
        order_by="student_group_name",
    )
    subjects = frappe.get_all(
        "Course",
        fields=["name", "course_name"],
        order_by="course_name",
    )
    grades = frappe.get_all(
        "Program",
        fields=["name", "program_name"],
        order_by="program_name",
    )

    program_course_rows = frappe.get_all(
        "Program Course",
        filters={"parenttype": "Program"},
        fields=["parent", "course", "course_name", "idx"],
        order_by="parent asc, idx asc",
    )
    program_courses = {}
    for row in program_course_rows:
        program_courses.setdefault(row.parent, []).append(
            {"course": row.course, "course_name": row.course_name or row.course}
        )

    context.wubet_boot = frappe.as_json(
        {
            "student_groups": student_groups,
            "subjects": subjects,
            "grades": grades,
            "default_academic_year": default_academic_year,
            "semesters": semester_options,
            "exam_options": exam_options,
            "program_courses": program_courses,
        }
    )
    
    # Ensure CSRF token is available in template context
    # Frappe automatically provides csrf_token in context, but we ensure it's set
    try:
        if not hasattr(context, 'csrf_token') or not context.csrf_token:
            # Try to get CSRF token from Frappe's standard locations
            if hasattr(frappe.local, 'form_dict') and frappe.local.form_dict.get('csrf_token'):
                context.csrf_token = frappe.local.form_dict.csrf_token
            elif frappe.session and hasattr(frappe.session, 'data') and frappe.session.data.get('csrf_token'):
                context.csrf_token = frappe.session.data.csrf_token
            elif hasattr(frappe.local, 'csrf_token'):
                context.csrf_token = frappe.local.csrf_token
    except Exception:
        # If we can't get the token, it will be retrieved from cookies on the frontend
        pass

    return context
