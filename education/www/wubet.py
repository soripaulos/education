import frappe
from frappe import _


def get_context(context):
    context.title = _("Student Result Entry")

    default_academic_year = "2018 E.C."
    semester_options = [
        {"label": "2018 E.C. (First Semester)", "value": "2018 E.C. (First Semester)"},
        {"label": "2018 E.C. (Second Semester)", "value": "2018 E.C. (Second Semester)"},
    ]
    exam_options = [
        {"label": "First Test", "value": "First Test", "max_score": 15},
        {"label": "Second Test", "value": "Second Test", "max_score": 15},
        {"label": "Mid Exam", "value": "Mid Exam", "max_score": 30},
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

    context.wubet_boot = frappe.as_json(
        {
            "student_groups": student_groups,
            "subjects": subjects,
            "grades": grades,
            "default_academic_year": default_academic_year,
            "semesters": semester_options,
            "exam_options": exam_options,
        }
    )

    return context
