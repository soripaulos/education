# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Every gap between applications, students, enrollments, sections, exits,
logins and exam results, one row per finding (see ``lifecycle.diagnostics``).
"""

import frappe
from frappe import _

from education.education.lifecycle.common import BLOCKED, INFO, REVIEW
from education.education.lifecycle.diagnostics import collect
from education.education.lifecycle.reconcile import get_previous_academic_year

CATEGORIES = [
	"Identity",
	"Promotion",
	"Enrollment",
	"Section",
	"Exit",
	"Status",
	"Account",
	"Exam",
	"Data Quality",
]


def execute(filters=None):
	filters = frappe._dict(filters or {})
	new_year = filters.academic_year or _latest_year()
	if not new_year:
		return [], []
	previous_year = filters.previous_academic_year or get_previous_academic_year(new_year)
	if not previous_year:
		frappe.throw(_("{0} has no earlier academic year to compare with.").format(new_year))

	findings = collect(new_year, previous_year, branch=filters.branch, program=filters.program)
	all_findings = findings
	if filters.severity:
		findings = [f for f in findings if f.severity == filters.severity]
	if filters.category:
		findings = [f for f in findings if f.category == filters.category]
	if filters.student:
		findings = [f for f in findings if f.student == filters.student]

	message = _(
		"Comparing {0} applications and enrollments with {1}. Blocked rows stop enrollment; Review rows need a decision; Info rows are worth knowing."
	).format(new_year, previous_year)
	return get_columns(), findings, message, get_chart(findings), get_summary(all_findings)


def _latest_year():
	rows = frappe.get_all("Academic Year", order_by="year_start_date desc", limit=1, pluck="name")
	return rows[0] if rows else None


def get_columns():
	return [
		{"label": _("Severity"), "fieldname": "severity", "fieldtype": "Data", "width": 80},
		{"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 100},
		{"label": _("Issue"), "fieldname": "issue", "fieldtype": "Data", "width": 420},
		{"label": _("Student"), "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 120},
		{"label": _("Student Name"), "fieldname": "student_name", "fieldtype": "Data", "width": 190},
		{"label": _("Applicant"), "fieldname": "student_applicant", "fieldtype": "Link", "options": "Student Applicant", "width": 110},
		{"label": _("Last Year"), "fieldname": "previous_program", "fieldtype": "Link", "options": "Program", "width": 110},
		{"label": _("This Year"), "fieldname": "new_program", "fieldtype": "Link", "options": "Program", "width": 110},
		{"label": _("Section"), "fieldname": "section", "fieldtype": "Data", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Data", "width": 110},
		{"label": _("What To Do"), "fieldname": "action", "fieldtype": "Data", "width": 300},
		{"label": _("Reference Type"), "fieldname": "reference_doctype", "fieldtype": "Link", "options": "DocType", "width": 130},
		{"label": _("Reference"), "fieldname": "reference_name", "fieldtype": "Dynamic Link", "options": "reference_doctype", "width": 150},
	]


def get_summary(findings):
	counts = {BLOCKED: 0, REVIEW: 0, INFO: 0}
	for f in findings:
		counts[f.severity] = counts.get(f.severity, 0) + 1
	students = len({f.student or f.student_applicant for f in findings if f.severity != INFO})
	return [
		{"value": counts[BLOCKED], "label": _("Blocked"), "indicator": "Red", "datatype": "Int"},
		{"value": counts[REVIEW], "label": _("Need Review"), "indicator": "Orange", "datatype": "Int"},
		{"value": counts[INFO], "label": _("Info"), "indicator": "Blue", "datatype": "Int"},
		{"value": students, "label": _("Students With Blocked/Review Issues"), "indicator": "Grey", "datatype": "Int"},
	]


def get_chart(findings):
	if not findings:
		return None
	counts = {}
	for f in findings:
		counts.setdefault(f.category, {BLOCKED: 0, REVIEW: 0, INFO: 0})
		counts[f.category][f.severity] = counts[f.category].get(f.severity, 0) + 1
	labels = [c for c in CATEGORIES if c in counts] + sorted(c for c in counts if c not in CATEGORIES)
	return {
		"data": {
			"labels": [_(label) for label in labels],
			"datasets": [
				{"name": _(severity), "values": [counts[label][severity] for label in labels]}
				for severity in (BLOCKED, REVIEW, INFO)
			],
		},
		"type": "bar",
		"barOptions": {"stacked": 1},
		"colors": ["#e24c4c", "#f5a524", "#5e9ae6"],
	}
