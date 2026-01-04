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
	columns = get_columns_sql(filters, subjects)
	
	# Generate chart
	chart = get_chart(data)
	
	# Generate message about exam selection
	message = get_report_message(filters)
	
	return columns, data, message, chart


def get_report_message(filters):
	"""
	Generate informational message about the report parameters
	"""
	selected_exams = filters.get("exam")
	if selected_exams and isinstance(selected_exams, str):
		import json
		try:
			selected_exams = json.loads(selected_exams)
		except:
			selected_exams = [e.strip() for e in selected_exams.split(",") if e.strip()]
	
	if not selected_exams:
		return _("Showing total scores from <b>all exams</b> for the selected filters.")
	elif len(selected_exams) == 1:
		return _("Showing individual scores for exam: <b>{0}</b>").format(selected_exams[0])
	else:
		exam_list = ", ".join(selected_exams)
		return _("Showing summed scores for exams: <b>{0}</b>").format(exam_list)


def get_subjects_sql(filters):
	"""
	Get all subjects (courses) from the Program linked to the Student Group
	"""
	student_group = filters.get("student_group")
	
	# Get the Program (Grade) from Student Group
	program = frappe.db.get_value("Student Group", student_group, "program")
	
	if not program:
		frappe.msgprint(_("No Program (Grade) linked to the selected Student Group"))
		return []
	
	# Get all courses from Program Course child table using SQL
	query = """
		SELECT course, course_name
		FROM `tabProgram Course`
		WHERE parent = %(program)s
		ORDER BY course_name
	"""
	
	courses = frappe.db.sql(query, {"program": program}, as_dict=True)
	
	if not courses:
		frappe.msgprint(_("No courses found in the Program '{0}'").format(program))
		return []
	
	return [c.course for c in courses]


def get_data_sql(filters, subjects):
	"""
	Fetch all data using a single optimized SQL query with pivot
	"""
	# Get selected exams (if any)
	selected_exams = filters.get("exam")
	if selected_exams and isinstance(selected_exams, str):
		import json
		try:
			selected_exams = json.loads(selected_exams)
		except:
			selected_exams = [e.strip() for e in selected_exams.split(",") if e.strip()]
	
	# Build conditions (include both draft and submitted)
	conditions = ["stsr.docstatus IN (0, 1)"]
	conditions.append("stsr.student_group = %(student_group)s")
	conditions.append("stsr.academic_year = %(academic_year)s")
	
	if filters.get("semester"):
		conditions.append("stsr.semester = %(semester)s")
	
	# Add exam filter if specified
	if selected_exams:
		exam_placeholders = ", ".join(["%s"] * len(selected_exams))
		conditions.append(f"stsr.exam IN ({exam_placeholders})")
	
	where_clause = " AND ".join(conditions)
	
	# Build subject sum columns dynamically
	subject_columns = []
	for subject in subjects:
		subject_key = frappe.scrub(subject)
		subject_columns.append(f"""
			SUM(CASE WHEN stsr.subject = '{subject}' THEN stsr.score ELSE 0 END) as `subject_{subject_key}`
		""")
	
	subject_sql = ",\n".join(subject_columns)
	
	# First, get all students in the student group
	students = frappe.get_all(
		"Student Group Student",
		filters={"parent": filters.get("student_group")},
		fields=["student", "student_name"],
		order_by="student_name"
	)
	
	if not students:
		frappe.msgprint(_("No students found in the selected student group"))
		return []
	
	# Main query with pivot logic - get results for students who have them
	query_params = {
		"student_group": filters.get("student_group"),
		"academic_year": filters.get("academic_year")
	}
	
	if filters.get("semester"):
		query_params["semester"] = filters.get("semester")
	
	query = f"""
		SELECT 
			stsr.student,
			MAX(stsr.student_name) as student_name,
			stsr.student_group,
			{subject_sql},
			SUM(stsr.score) as total,
			COUNT(stsr.name) as exam_entries
		FROM `tabStudent Term Subject Result` stsr
		WHERE {where_clause}
		GROUP BY stsr.student, stsr.student_group
	"""
	
	# Execute query with parameters
	if selected_exams:
		# Add exam values to parameters
		results_data = frappe.db.sql(query, tuple(list(query_params.values()) + selected_exams), as_dict=True)
	else:
		results_data = frappe.db.sql(query, query_params, as_dict=True)
	
	# Create a dict for quick lookup
	results_dict = {row.student: row for row in results_data}
	
	# Build final data including all students (even those without results)
	data = []
	for student in students:
		if student.student in results_dict:
			row = results_dict[student.student]
		else:
			# Student has no results yet, create empty row
			row = frappe._dict({
				"student": student.student,
				"student_name": student.student_name,
				"student_group": filters.get("student_group"),
				"total": 0,
				"exam_entries": 0
			})
			# Initialize all subject columns to 0
			for subject in subjects:
				subject_key = "subject_" + frappe.scrub(subject)
				row[subject_key] = 0
		
		# Calculate average (divided by total subjects in program)
		row.average = round(row.total / len(subjects), 2) if len(subjects) > 0 else 0
		
		data.append(row)
	
	# Calculate average exam entries to identify incomplete data
	if data:
		exam_entries_list = [row.exam_entries for row in data if row.exam_entries > 0]
		avg_exam_entries = sum(exam_entries_list) / len(exam_entries_list) if exam_entries_list else 0
		
		# Mark students with below-average exam entries
		for row in data:
			if row.exam_entries < avg_exam_entries * 0.7:  # Less than 70% of average
				row.completion_status = "⚠ Incomplete"
			elif row.exam_entries == 0:
				row.completion_status = "❌ No Data"
			else:
				row.completion_status = "✓ Complete"
	
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


def get_columns_sql(filters, subjects):
	"""
	Generate column definitions
	"""
	# Get selected exams
	selected_exams = filters.get("exam")
	if selected_exams and isinstance(selected_exams, str):
		import json
		try:
			selected_exams = json.loads(selected_exams)
		except:
			selected_exams = [e.strip() for e in selected_exams.split(",") if e.strip()]
	
	# Check if single exam is selected
	is_single_exam = selected_exams and len(selected_exams) == 1
	
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
		subject_label = subject
		if is_single_exam:
			# Add exam name to column label for single exam
			subject_label = f"{subject} ({selected_exams[0]})"
		
		columns.append({
			"fieldname": "subject_" + frappe.scrub(subject),
			"label": subject_label,
			"fieldtype": "Float",
			"width": 120 if is_single_exam else 100,
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
		},
		{
			"fieldname": "exam_entries",
			"label": _("Exam Count"),
			"fieldtype": "Int",
			"width": 90
		},
		{
			"fieldname": "completion_status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 120
		}
	])
	
	return columns


def get_chart(data):
	"""
	Generate performance distribution chart
	"""
	if not data:
		return None
	
	# Performance Distribution Chart
	ranges = {
		"90-100": 0,
		"80-89": 0,
		"70-79": 0,
		"60-69": 0,
		"50-59": 0,
		"Below 50": 0
	}
	
	for row in data:
		avg = row.average
		if avg >= 90:
			ranges["90-100"] += 1
		elif avg >= 80:
			ranges["80-89"] += 1
		elif avg >= 70:
			ranges["70-79"] += 1
		elif avg >= 60:
			ranges["60-69"] += 1
		elif avg >= 50:
			ranges["50-59"] += 1
		else:
			ranges["Below 50"] += 1
	
	chart = {
		"data": {
			"labels": list(ranges.keys()),
			"datasets": [
				{
					"name": "Number of Students",
					"values": list(ranges.values())
				}
			]
		},
		"type": "bar",
		"colors": ["#29CD42"],
		"title": "Performance Distribution by Average Score"
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
