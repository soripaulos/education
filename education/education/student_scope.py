# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Students (and the parents who use their login) only see their own records.

The Student role can read Teacher Parent Message, Student Hub Evaluation and
Student Discipline Incident, but nothing narrowed that to the signed-in
student, so the student app listed every student's messages and reports.
These hooks add that filter. Staff are not affected; their own scoping lives
in the site's "MBS - ... Scope" server scripts.
"""

import frappe

# Anyone holding one of these is staff and is never narrowed here.
STAFF_ROLES = {
    "System Manager",
    "Administrator",
    "Academics User",
    "Education Manager",
    "Director",
    "Instructor",
    "DD Student Registrar",
}


def student_for_user(user):
    """The Student record behind a student-app login, or None for staff."""
    if not user or user in ("Administrator", "Guest"):
        return None
    if STAFF_ROLES.intersection(frappe.get_roles(user)):
        return None
    return frappe.db.get_value("Student", {"user": user}, "name")


def _conditions(doctype, user):
    student = student_for_user(user or frappe.session.user)
    if not student:
        return ""
    return f"`tab{doctype}`.student = {frappe.db.escape(student)}"


def _has_permission(doc, user):
    student = student_for_user(user or frappe.session.user)
    if not student:
        return True
    return doc.get("student") == student


def teacher_parent_message_query(user=None):
    return _conditions("Teacher Parent Message", user)


def teacher_parent_message_permission(doc, ptype=None, user=None):
    return _has_permission(doc, user)


def hub_evaluation_query(user=None):
    return _conditions("Student Hub Evaluation", user)


def hub_evaluation_permission(doc, ptype=None, user=None):
    return _has_permission(doc, user)


def discipline_incident_query(user=None):
    return _conditions("Student Discipline Incident", user)


def discipline_incident_permission(doc, ptype=None, user=None):
    return _has_permission(doc, user)
