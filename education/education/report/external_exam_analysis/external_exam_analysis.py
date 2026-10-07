# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Grade 6 / Grade 8 regional and Grade 12 national exam results: one row
per student with a column per subject, plus pass rates and subject averages.
"""

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.exam_type:
		return [], []

	conditions = {"exam_type": filters.exam_type, "docstatus": 1}
	if filters.academic_year:
		conditions["academic_year"] = filters.academic_year
	if filters.program:
		conditions["program"] = filters.program
	if filters.student_group:
		conditions["student_group"] = filters.student_group

	results = frappe.get_all(
		"External Exam Result",
		filters=conditions,
		fields=[
			"name",
			"student",
			"student_name",
			"school_id",
			"gender",
			"academic_year",
			"program",
			"student_group",
			"stream",
			"total_score",
			"total_max_score",
			"average_percentage",
			"result_status",
		],
		order_by="average_percentage desc",
		limit_page_length=0,
	)
	subjects = frappe.get_all(
		"External Exam Subject",
		filters={"parent": ["in", [r.name for r in results] or [""]], "parenttype": "External Exam Result"},
		fields=["parent", "subject", "score", "max_score", "percentage"],
		order_by="idx",
		limit_page_length=0,
	)

	subject_order = []
	by_result = {}
	for row in subjects:
		if row.subject not in subject_order:
			subject_order.append(row.subject)
		by_result.setdefault(row.parent, {})[row.subject] = row

	data = []
	for rank, result in enumerate(results, 1):
		line = frappe._dict(result)
		line.rank = rank
		for subject in subject_order:
			cell = by_result.get(result.name, {}).get(subject)
			line[_key(subject)] = flt(cell.score) if cell else None
		data.append(line)

	return (
		get_columns(subject_order),
		data,
		None,
		get_chart(subject_order, subjects),
		get_summary(results),
	)


def _key(subject):
	return "subject_" + frappe.scrub(subject)


def get_columns(subjects):
	columns = [
		{"label": _("Rank"), "fieldname": "rank", "fieldtype": "Int", "width": 60},
		{"label": _("Record"), "fieldname": "name", "fieldtype": "Link", "options": "External Exam Result", "width": 130},
		{"label": _("Student"), "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 120},
		{"label": _("Student Name"), "fieldname": "student_name", "fieldtype": "Data", "width": 190},
		{"label": _("Gender"), "fieldname": "gender", "fieldtype": "Data", "width": 70},
		{"label": _("Program"), "fieldname": "program", "fieldtype": "Link", "options": "Program", "width": 110},
		{"label": _("Section"), "fieldname": "student_group", "fieldtype": "Link", "options": "Student Group", "width": 110},
	]
	columns += [
		{"label": subject, "fieldname": _key(subject), "fieldtype": "Float", "width": 100, "precision": 1}
		for subject in subjects
	]
	columns += [
		{"label": _("Total"), "fieldname": "total_score", "fieldtype": "Float", "width": 80, "precision": 1},
		{"label": _("Out Of"), "fieldname": "total_max_score", "fieldtype": "Float", "width": 70, "precision": 0},
		{"label": _("Average"), "fieldname": "average_percentage", "fieldtype": "Percent", "width": 90},
		{"label": _("Result"), "fieldname": "result_status", "fieldtype": "Data", "width": 80},
	]
	return columns


def get_summary(results):
	sat = [r for r in results if r.result_status not in ("Absent", "Withheld")]
	passed = sum(1 for r in sat if r.result_status == "Pass")
	failed = sum(1 for r in sat if r.result_status == "Fail")
	averages = [flt(r.average_percentage) for r in sat if r.result_status in ("Pass", "Fail")]
	return [
		{"value": len(results), "label": _("Results"), "datatype": "Int", "indicator": "Grey"},
		{"value": passed, "label": _("Passed"), "datatype": "Int", "indicator": "Green"},
		{"value": failed, "label": _("Failed"), "datatype": "Int", "indicator": "Red"},
		{
			"value": passed / (passed + failed) * 100 if (passed + failed) else 0,
			"label": _("Pass Rate"),
			"datatype": "Percent",
			"indicator": "Blue",
		},
		{
			"value": sum(averages) / len(averages) if averages else 0,
			"label": _("Mean Average"),
			"datatype": "Percent",
			"indicator": "Blue",
		},
	]


def get_chart(subject_order, subjects):
	if not subject_order:
		return None
	totals = {}
	for row in subjects:
		totals.setdefault(row.subject, []).append(flt(row.percentage))
	return {
		"data": {
			"labels": subject_order,
			"datasets": [
				{
					"name": _("Average %"),
					"values": [round(sum(totals[s]) / len(totals[s]), 1) for s in subject_order],
				}
			],
		},
		"type": "bar",
		"colors": ["#5e9ae6"],
	}
