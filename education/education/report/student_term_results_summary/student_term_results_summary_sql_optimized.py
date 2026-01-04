# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
# SQL-OPTIMIZED VERSION for better performance with large datasets

import frappe
from frappe import _


def execute(filters=None):
	"""
	SQL-optimized version using a single complex query
	Better performance for large datasets
	"""
	if not filters:
		return [], [], None, None
	
	if not filters.get("student_group"):
		frappe.throw(_("Please select a Student Group"))
	
	if not filters.get("academic_year"):
		frappe.throw(_("Please select an Academic Year"))
	
	# Get subjects first
	subjects = get_subjects_sql(filters)
	
	if not subjects:
		frappe.msgprint(_("No subjects found for the selected student group"))
		return [], []
	
	# Get data using optimized SQL query
	data = get_data_sql(filters, subjects)
	
	# Get dynamic columns
	columns = get_columns_sql(subjects)
	
	# Generate chart
	chart = get_chart(data)
	
	return columns, data, None, chart


def get_subjects_sql(filters):
	"""
	Get all unique subjects using a single SQL query
	"""
	conditions = ["docstatus = 1"]
	conditions.append("student_group = %(student_group)s")
	conditions.append("academic_year = %(academic_year)s")
	
	if filters.get("semester"):
		conditions.append("semester = %(semester)s")
	
	where_clause = " AND ".join(conditions)
	
	query = f"""
		SELECT DISTINCT subject
		FROM `tabStudent Term Subject Result`
		WHERE {where_clause}
		ORDER BY subject
	"""
	
	results = frappe.db.sql(query, filters, as_dict=True)
	return [r.subject for r in results]


def get_data_sql(filters, subjects):
	"""
	Fetch all data using a single optimized SQL query with pivot
	"""
	# Build conditions
	conditions = ["stsr.docstatus = 1"]
	conditions.append("stsr.student_group = %(student_group)s")
	conditions.append("stsr.academic_year = %(academic_year)s")
	
	if filters.get("semester"):
		conditions.append("stsr.semester = %(semester)s")
	
	where_clause = " AND ".join(conditions)
	
	# Build subject sum columns dynamically
	subject_columns = []
	for subject in subjects:
		subject_key = frappe.scrub(subject)
		subject_columns.append(f"""
			SUM(CASE WHEN stsr.subject = '{subject}' THEN stsr.score ELSE 0 END) as `subject_{subject_key}`
		""")
	
	subject_sql = ",\n".join(subject_columns)
	
	# Main query with pivot logic
	query = f"""
		SELECT 
			stsr.student,
			MAX(stsr.student_name) as student_name,
			stsr.student_group,
			{subject_sql},
			SUM(stsr.score) as total
		FROM `tabStudent Term Subject Result` stsr
		WHERE {where_clause}
		GROUP BY stsr.student, stsr.student_group
		ORDER BY stsr.student_name
	"""
	
	data = frappe.db.sql(query, filters, as_dict=True)
	
	# Calculate averages and prepare for ranking
	for row in data:
		# Count non-zero subjects
		subject_count = sum(1 for subject in subjects 
			if row.get("subject_" + frappe.scrub(subject), 0) > 0)
		
		# Calculate average
		row.average = round(row.total / subject_count, 2) if subject_count > 0 else 0
	
	# Calculate ranks
	data = calculate_ranks_sql(data)
	
	return data


def calculate_ranks_sql(data):
	"""
	Calculate ranks using SQL-like logic
	More efficient than Python sorting for large datasets
	"""
	# Sort by average descending
	sorted_data = sorted(data, key=lambda x: x.average, reverse=True)
	
	# Assign ranks (same average = same rank)
	current_rank = 1
	previous_average = None
	
	for i, row in enumerate(sorted_data):
		if previous_average is not None and row.average < previous_average:
			current_rank = i + 1
		row.rank = current_rank
		previous_average = row.average
	
	return data


def get_columns_sql(subjects):
	"""
	Generate column definitions
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
	
	# Add subject columns
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


def get_chart(data):
	"""
	Generate chart for visualization
	"""
	if not data:
		return None
	
	# Get top 10 students
	top_students = sorted(data, key=lambda x: x.average, reverse=True)[:10]
	
	labels = [row.student_name for row in top_students]
	averages = [row.average for row in top_students]
	
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


# Alternative: Pure SQL with Window Functions (for advanced users)
def get_data_with_window_functions(filters, subjects):
	"""
	Most optimized version using SQL window functions for ranking
	Requires MariaDB 10.2+ or MySQL 8.0+
	"""
	conditions = ["stsr.docstatus = 1"]
	conditions.append("stsr.student_group = %(student_group)s")
	conditions.append("stsr.academic_year = %(academic_year)s")
	
	if filters.get("semester"):
		conditions.append("stsr.semester = %(semester)s")
	
	where_clause = " AND ".join(conditions)
	
	# Build subject columns
	subject_columns = []
	for subject in subjects:
		subject_key = frappe.scrub(subject)
		subject_columns.append(f"""
			SUM(CASE WHEN stsr.subject = '{subject}' THEN stsr.score ELSE 0 END) as `subject_{subject_key}`
		""")
	
	subject_sql = ",\n".join(subject_columns)
	
	# Query with window function for ranking
	query = f"""
		WITH StudentScores AS (
			SELECT 
				stsr.student,
				MAX(stsr.student_name) as student_name,
				stsr.student_group,
				{subject_sql},
				SUM(stsr.score) as total,
				COUNT(DISTINCT stsr.subject) as subject_count
			FROM `tabStudent Term Subject Result` stsr
			WHERE {where_clause}
			GROUP BY stsr.student, stsr.student_group
		),
		StudentAverages AS (
			SELECT 
				*,
				ROUND(total / subject_count, 2) as average
			FROM StudentScores
		)
		SELECT 
			*,
			DENSE_RANK() OVER (ORDER BY average DESC) as rank
		FROM StudentAverages
		ORDER BY rank, student_name
	"""
	
	try:
		data = frappe.db.sql(query, filters, as_dict=True)
		return data
	except Exception as e:
		# Fallback to regular method if window functions not supported
		frappe.log_error(f"Window function not supported: {str(e)}")
		return get_data_sql(filters, subjects)
