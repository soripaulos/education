import frappe
from frappe import _

no_cache = 1


def get_context(context):
    context.title = _("Student Result Entry")

    # Get CSRF token from Frappe's standard locations
    csrf_token = None
    if hasattr(frappe.local, 'form_dict') and frappe.local.form_dict.get('csrf_token'):
        csrf_token = frappe.local.form_dict.get('csrf_token')
    elif hasattr(frappe, 'session') and hasattr(frappe.session, 'data'):
        csrf_token = frappe.session.data.get('csrf_token')
    elif hasattr(frappe.local, 'csrf_token'):
        csrf_token = frappe.local.csrf_token
    
    # Set CSRF token in context
    context.csrf_token = csrf_token or ""

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
        limit_page_length=0,
    )

    # Some Student Groups need subject lists from a different Program.
    # Example: "Nursery I" should use the same subjects as "Nursery AO".
    # We keep `program` intact (used for grade/program display), and add a
    # separate `subject_program` key used only for subject filtering on /wubet.
    def _normalize_label(value: str) -> str:
        return " ".join((value or "").strip().lower().replace("-", " ").split())

    for group in student_groups:
        label = _normalize_label(group.get("student_group_name") or group.get("name") or "")
        if label in {"nursery i", "nursery 1"}:
            group["subject_program"] = "Nursery AO"
    
    # Get all courses with their associated programs for filtering
    subjects = frappe.get_all(
        "Course",
        fields=["name", "course_name"],
        order_by="course_name",
        limit_page_length=0,
    )
    
    # Get program courses mapping
    program_courses = {}
    for program in frappe.get_all("Program", fields=["name"], limit_page_length=0):
        courses = frappe.get_all(
            "Program Course",
            filters={
                "parent": program.name,
                "parenttype": "Program",
                "parentfield": "courses",
            },
            fields=["course"],
            pluck="course",
            limit_page_length=0,
        )
        program_courses[program.name] = courses
    
    grades = frappe.get_all(
        "Program",
        fields=["name", "program_name"],
        order_by="program_name",
        limit_page_length=0,
    )

    context.wubet_boot = frappe.as_json(
        {
            "student_groups": student_groups,
            "subjects": subjects,
            "grades": grades,
            "program_courses": program_courses,
            "default_academic_year": default_academic_year,
            "semesters": semester_options,
            "exam_options": exam_options,
        }
    )

    return context
