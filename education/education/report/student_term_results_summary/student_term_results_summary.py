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
	
	# Get selected exams (if any)
	selected_exams = filters.get("exam")
	if selected_exams and isinstance(selected_exams, str):
		# Parse MultiSelectList format
		import json
		try:
			selected_exams = json.loads(selected_exams)
		except:
			selected_exams = [e.strip() for e in selected_exams.split(",") if e.strip()]
	
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
			"docstatus": ["in", [0, 1]]  # Include both draft and submitted results
		}
		
		if filters.get("semester"):
			result_conditions["semester"] = filters.get("semester")
		
		# Add exam filter if specified
		if selected_exams:
			result_conditions["exam"] = ["in", selected_exams]
		
		results = frappe.get_all(
			"Student Term Subject Result",
			filters=result_conditions,
			fields=["subject", "exam", "score", "max_score", "docstatus"]
		)
		
		# Count total exam entries for this student
		total_exam_entries = len(results)
		
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
		
		# Add subject scores to the row
		for subject in subjects:
			subject_key = "subject_" + frappe.scrub(subject)
			if subject in subject_totals:
				total_score = subject_totals[subject]["total_score"]
				row[subject_key] = total_score
				grand_total += total_score
			else:
				row[subject_key] = 0
		
		# Calculate total and average
		row.total = grand_total
		# Average divided by total number of subjects in the program
		row.average = round(grand_total / len(subjects), 2) if len(subjects) > 0 else 0
		row.exam_entries = total_exam_entries  # Track number of exam entries
		
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
	
	# Calculate ranks based on average
	data = calculate_ranks(data)
	
	return data


def get_subjects_for_group(filters):
	"""
	Get all subjects (courses) from the Program linked to the Student Group
	"""
	student_group = filters.get("student_group")
	
	# Get the Program (Grade) from Student Group
	program = frappe.db.get_value("Student Group", student_group, "program")
	
	if not program:
		frappe.msgprint(_("No Program (Grade) linked to the selected Student Group"))
		return []
	
	# Get all courses from Program Course child table
	courses = frappe.get_all(
		"Program Course",
		filters={"parent": program},
		fields=["course", "course_name"],
		order_by="course_name"
	)
	
	if not courses:
		frappe.msgprint(_("No courses found in the Program '{0}'").format(program))
		return []
	
	# Return list of course names
	return [c.course for c in courses]


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
	
	# Get subjects dynamically
	subjects = get_subjects_for_group(filters)
	
	# Add columns for each subject
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
	Generate multiple practical charts for visualization
	Returns the first chart (performance distribution)
	"""
	if not data:
		return None
	
	# Chart 1: Performance Distribution (Grade Ranges)
	performance_chart = get_performance_distribution_chart(data)
	
	return performance_chart


def get_performance_distribution_chart(data):
	"""
	Chart showing distribution of students across performance ranges
	"""
	# Define grade ranges
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


def get_subject_comparison_chart(data, subjects):
	"""
	Chart showing average performance across subjects
	"""
	subject_averages = {}
	subject_counts = {}
	
	for subject in subjects:
		subject_key = "subject_" + frappe.scrub(subject)
		total = 0
		count = 0
		
		for row in data:
			score = row.get(subject_key, 0)
			if score > 0:
				total += score
				count += 1
		
		if count > 0:
			subject_averages[subject] = round(total / count, 2)
			subject_counts[subject] = count
	
	# Sort subjects by average (descending)
	sorted_subjects = sorted(subject_averages.items(), key=lambda x: x[1], reverse=True)
	
	chart = {
		"data": {
			"labels": [s[0] for s in sorted_subjects],
			"datasets": [
				{
					"name": "Average Score",
					"values": [s[1] for s in sorted_subjects]
				}
			]
		},
		"type": "bar",
		"colors": ["#7575FF"],
		"title": "Subject Performance Comparison"
	}
	
	return chart


def get_completion_status_chart(data):
	"""
	Chart showing distribution of completion status
	"""
	status_counts = {
		"Complete": 0,
		"Incomplete": 0,
		"No Data": 0
	}
	
	for row in data:
		status = row.get("completion_status", "")
		if "Complete" in status:
			status_counts["Complete"] += 1
		elif "Incomplete" in status:
			status_counts["Incomplete"] += 1
		elif "No Data" in status:
			status_counts["No Data"] += 1
	
	chart = {
		"data": {
			"labels": list(status_counts.keys()),
			"datasets": [
				{
					"name": "Number of Students",
					"values": list(status_counts.values())
				}
			]
		},
		"type": "donut",
		"colors": ["#29CD42", "#FFA00A", "#F06060"],
		"title": "Data Completion Status"
	}
	
	return chart
