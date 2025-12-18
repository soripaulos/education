import frappe
from frappe import _


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
            filters={"parent": program.name},
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
