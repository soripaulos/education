# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	"""
	Main execution function for the report
	Returns: columns, data, message, chart, report_summary
	"""
	if not filters:
		return [], [], None, None
	
	if not filters.get("student_group"):
		frappe.throw(_("Please select a Student Group"))
	
	if not filters.get("academic_year"):
		frappe.throw(_("Please select an Academic Year"))
	
	# Get data using complex SQL query
	data = get_data(filters)
	
	# Get dynamic columns based on subjects
	columns = get_columns(filters)
	
	# Generate chart
	chart = get_chart(data)
	
	return columns, data, None, chart


def get_data(filters):
	"""
	Fetch data using complex SQL query and process it
	"""
	# Build the base SQL query
	conditions = get_conditions(filters)
	
	# Get all subjects for the selected student group
	subjects = get_subjects_for_group(filters)
	
	if not subjects:
		frappe.msgprint(_("No subjects found for the selected student group"))
		return []
	
	# Get all students in the student group
	students = frappe.get_all(
		"Student Group Student",
		filters={"parent": filters.get("student_group")},
		fields=["student", "student_name"],
		order_by="student_name"
	)
	
	if not students:
		frappe.msgprint(_("No students found in the selected student group"))
		return []
	
	# Prepare data structure
	data = []
	
	for student in students:
		row = frappe._dict()
		row.student = student.student
		row.student_name = student.student_name
		row.student_group = filters.get("student_group")
		
		# Get all results for this student
		result_conditions = {
			"student": student.student,
			"student_group": filters.get("student_group"),
			"academic_year": filters.get("academic_year"),
			"docstatus": 1  # Only submitted results
		}
		
		if filters.get("semester"):
			result_conditions["semester"] = filters.get("semester")
		
		results = frappe.get_all(
			"Student Term Subject Result",
			filters=result_conditions,
			fields=["subject", "exam", "score", "max_score"]
		)
		
		# Group results by subject and sum up all exam scores
		subject_totals = {}
		for result in results:
			subject = result.subject
			if subject not in subject_totals:
				subject_totals[subject] = {
					"total_score": 0,
					"total_max_score": 0
				}
			subject_totals[subject]["total_score"] += result.score or 0
			subject_totals[subject]["total_max_score"] += result.max_score or 0
		
		# Calculate totals for the row
		grand_total = 0
		subject_count = 0
		
		# Add subject scores to the row
		for subject in subjects:
			subject_key = "subject_" + frappe.scrub(subject)
			if subject in subject_totals:
				total_score = subject_totals[subject]["total_score"]
				row[subject_key] = total_score
				grand_total += total_score
				subject_count += 1
			else:
				row[subject_key] = 0
		
		# Calculate total, average, and percentage
		row.total = grand_total
		row.average = round(grand_total / subject_count, 2) if subject_count > 0 else 0
		
		data.append(row)
	
	# Calculate ranks based on average
	data = calculate_ranks(data)
	
	return data


def get_subjects_for_group(filters):
	"""
	Get all unique subjects (courses) for the selected student group
	"""
	conditions = {
		"student_group": filters.get("student_group"),
		"academic_year": filters.get("academic_year"),
		"docstatus": 1
	}
	
	if filters.get("semester"):
		conditions["semester"] = filters.get("semester")
	
	subjects = frappe.get_all(
		"Student Term Subject Result",
		filters=conditions,
		fields=["subject"],
		distinct=True,
		order_by="subject"
	)
	
	return [s.subject for s in subjects]


def get_conditions(filters):
	"""
	Build SQL conditions based on filters
	"""
	conditions = []
	
	if filters.get("student_group"):
		conditions.append("student_group = %(student_group)s")
	
	if filters.get("academic_year"):
		conditions.append("academic_year = %(academic_year)s")
	
	if filters.get("semester"):
		conditions.append("semester = %(semester)s")
	
	conditions.append("docstatus = 1")
	
	return " AND ".join(conditions) if conditions else "1=1"


def get_columns(filters):
	"""
	Generate dynamic columns based on subjects
	"""
	columns = [
		{
			"fieldname": "student",
			"label": _("Student ID"),
			"fieldtype": "Link",
			"options": "Student",
			"width": 120
		},
		{
			"fieldname": "student_name",
			"label": _("Student Name"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "student_group",
			"label": _("Student Group"),
			"fieldtype": "Link",
			"options": "Student Group",
			"width": 150
		}
	]
	
	# Get subjects dynamically
	subjects = get_subjects_for_group(filters)
	
	# Add columns for each subject
	for subject in subjects:
		columns.append({
			"fieldname": "subject_" + frappe.scrub(subject),
			"label": subject,
			"fieldtype": "Float",
			"width": 100,
			"precision": 2
		})
	
	# Add summary columns
	columns.extend([
		{
			"fieldname": "total",
			"label": _("Total"),
			"fieldtype": "Float",
			"width": 100,
			"precision": 2
		},
		{
			"fieldname": "average",
			"label": _("Average"),
			"fieldtype": "Float",
			"width": 100,
			"precision": 2
		},
		{
			"fieldname": "rank",
			"label": _("Rank"),
			"fieldtype": "Int",
			"width": 80
		}
	])
	
	return columns


def calculate_ranks(data):
	"""
	Calculate ranks based on average scores
	Students with same average get the same rank
	"""
	# Sort by average (descending)
	sorted_data = sorted(data, key=lambda x: x.average, reverse=True)
	
	# Assign ranks
	current_rank = 1
	previous_average = None
	
	for i, row in enumerate(sorted_data):
		if previous_average is not None and row.average < previous_average:
			current_rank = i + 1
		row.rank = current_rank
		previous_average = row.average
	
	return data


def get_chart(data):
	"""
	Generate chart for visualization
	"""
	if not data:
		return None
	
	# Get student names and averages for chart
	labels = [row.student_name for row in data[:10]]  # Limit to top 10 for readability
	averages = [row.average for row in data[:10]]
	
	chart = {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Average Score",
					"values": averages
				}
			]
		},
		"type": "bar",
		"colors": ["#29CD42"],
		"barOptions": {
			"stacked": False
		}
	}
	
	return chart
