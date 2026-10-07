# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Per grade: how last year's class carried over, and how this year is filling.

"Last year" columns follow the students who were in the grade last year
(how many applied to come back, how many repeat, how many are leaving).
"This year" columns count the applications and enrollments for the grade in
the new year, new and returning together.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt

from education.education.lifecycle.common import grade_index, is_final_grade
from education.education.lifecycle.reconcile import Context, get_previous_academic_year


def execute(filters=None):
	filters = frappe._dict(filters or {})
	new_year = filters.academic_year or _latest_year()
	if not new_year:
		return [], []
	previous_year = filters.previous_academic_year or get_previous_academic_year(new_year)
	if not previous_year:
		frappe.throw(_("{0} has no earlier academic year to compare with.").format(new_year))

	ctx = Context(previous_year, new_year)
	data = get_data(ctx, filters.branch)
	return get_columns(previous_year, new_year), data, None, get_chart(data), get_summary(data)


def _latest_year():
	rows = frappe.get_all("Academic Year", order_by="year_start_date desc", limit=1, pluck="name")
	return rows[0] if rows else None


def _blank(program):
	return frappe._dict(
		program=program,
		prev_enrolled=0,
		returning=0,
		repeating=0,
		leaving=0,
		retention=0.0,
		applied=0,
		applied_existing=0,
		applied_new=0,
		enrolled=0,
		pending=0,
		male=0,
		female=0,
		unpaid=0,
		sections=0,
	)


def get_data(ctx, branch=None):
	rows = {}

	def row(program):
		return rows.setdefault(program, _blank(program))

	applicant_program = {}
	for app in ctx.applicants:
		if branch and app.branch != branch:
			continue
		applicant_program.setdefault(app.sid, app.program)

	# Last year's class, followed forward.
	for student_name, enrollments in ctx.prev_enrollments.items():
		student = ctx.students.get(student_name)
		if not student:
			continue
		if branch and ctx.branch_of(student) != branch:
			continue
		program = enrollments[0].program
		r = row(program)
		r.prev_enrolled += 1
		new_program = applicant_program.get(student.sid)
		if new_program or student_name in ctx.new_enrollments:
			r.returning += 1
			if new_program == program:
				r.repeating += 1
		else:
			r.leaving += 1

	# This year's grade.
	sections = {}
	for app in ctx.applicants:
		if branch and app.branch != branch:
			continue
		r = row(app.program)
		r.applied += 1
		if app.applicant_type == "Existing":
			r.applied_existing += 1
		else:
			r.applied_new += 1
		gender = (app.gender or "").lower()
		if gender == "male":
			r.male += 1
		elif gender == "female":
			r.female += 1
		if not cint(app.paid):
			r.unpaid += 1
		student = ctx.students_by_sid.get(app.sid)
		enrollments = ctx.new_enrollments.get(student.name, []) if student else []
		submitted = [e for e in enrollments if e.docstatus == 1]
		if submitted:
			r.enrolled += 1
			section = submitted[0].get("student_group")
			if section:
				sections.setdefault(app.program, set()).add(section)
		else:
			r.pending += 1

	for program, names in sections.items():
		rows[program].sections = len(names)
	for r in rows.values():
		r.retention = flt(r.returning) / r.prev_enrolled * 100 if r.prev_enrolled else 0.0
		r.graduating = is_final_grade(r.program)

	return sorted(
		rows.values(),
		key=lambda r: (grade_index(r.program) if grade_index(r.program) is not None else 99, r.program or ""),
	)


def get_columns(previous_year, new_year):
	last = _("{0}").format(previous_year)
	this = _("{0}").format(new_year)
	return [
		{"label": _("Program"), "fieldname": "program", "fieldtype": "Link", "options": "Program", "width": 130},
		{"label": _("Enrolled ({0})").format(last), "fieldname": "prev_enrolled", "fieldtype": "Int", "width": 120},
		{"label": _("Coming Back"), "fieldname": "returning", "fieldtype": "Int", "width": 110},
		{"label": _("Repeating"), "fieldname": "repeating", "fieldtype": "Int", "width": 95},
		{"label": _("Not Returning"), "fieldname": "leaving", "fieldtype": "Int", "width": 115},
		{"label": _("Retention %"), "fieldname": "retention", "fieldtype": "Percent", "width": 105},
		{"label": _("Applied ({0})").format(this), "fieldname": "applied", "fieldtype": "Int", "width": 120},
		{"label": _("Existing"), "fieldname": "applied_existing", "fieldtype": "Int", "width": 85},
		{"label": _("New"), "fieldname": "applied_new", "fieldtype": "Int", "width": 70},
		{"label": _("Enrolled ({0})").format(this), "fieldname": "enrolled", "fieldtype": "Int", "width": 120},
		{"label": _("Not Yet Enrolled"), "fieldname": "pending", "fieldtype": "Int", "width": 125},
		{"label": _("Sections"), "fieldname": "sections", "fieldtype": "Int", "width": 85},
		{"label": _("Male"), "fieldname": "male", "fieldtype": "Int", "width": 70},
		{"label": _("Female"), "fieldname": "female", "fieldtype": "Int", "width": 75},
		{"label": _("Unpaid Applications"), "fieldname": "unpaid", "fieldtype": "Int", "width": 140},
	]


def get_summary(data):
	total = lambda key: sum(cint(r[key]) for r in data)  # noqa: E731
	prev = total("prev_enrolled")
	returning = total("returning")
	graduating = sum(cint(r.prev_enrolled) for r in data if r.graduating)
	leaving = total("leaving") - graduating
	continuing = prev - graduating
	return [
		{"value": prev, "label": _("Enrolled Last Year"), "datatype": "Int", "indicator": "Grey"},
		{
			"value": flt(returning) / continuing * 100 if continuing else 0,
			"label": _("Retention (excl. Grade 12)"),
			"datatype": "Percent",
			"indicator": "Green",
		},
		{"value": max(leaving, 0), "label": _("Not Returning"), "datatype": "Int", "indicator": "Orange"},
		{"value": graduating, "label": _("Graduating"), "datatype": "Int", "indicator": "Purple"},
		{"value": total("applied_new"), "label": _("New Applicants"), "datatype": "Int", "indicator": "Blue"},
		{"value": total("enrolled"), "label": _("Enrolled This Year"), "datatype": "Int", "indicator": "Green"},
		{"value": total("pending"), "label": _("Not Yet Enrolled"), "datatype": "Int", "indicator": "Red"},
	]


def get_chart(data):
	if not data:
		return None
	return {
		"data": {
			"labels": [r.program for r in data],
			"datasets": [
				{"name": _("Enrolled last year"), "values": [r.prev_enrolled for r in data]},
				{"name": _("Applied this year"), "values": [r.applied for r in data]},
				{"name": _("Enrolled this year"), "values": [r.enrolled for r in data]},
			],
		},
		"type": "bar",
		"colors": ["#98a2b3", "#5e9ae6", "#2fb36d"],
	}
