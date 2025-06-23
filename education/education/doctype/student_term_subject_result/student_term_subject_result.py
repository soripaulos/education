# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class StudentTermSubjectResult(Document):
	def validate(self):
		self.validate_duplicate()
		self.calculate_percentage()
		self.validate_score()

	def validate_duplicate(self):
		"""Prevent duplicate results for same student, subject, exam type, and semester"""
		# Use the actual field names from user's doctype
		existing = frappe.db.exists("Student Term Subject Result", {
			"student": self.student,
			"subject": self.subject,
			"exam": self.exam,  # user's field name for assessment criteria
			"semester": self.semester,  # user's field name for academic term
			"academic_year": self.academic_year,
			"name": ["!=", self.name],
			"docstatus": ["!=", 2]
		})
		
		if existing:
			student_name = frappe.db.get_value("Student", self.student, "student_name") or self.student
			frappe.throw(
				f"Result already exists for {student_name} in {self.subject} "
				f"for {self.exam} in {self.semester}"
			)

	def calculate_percentage(self):
		"""Calculate percentage based on score and max score"""
		# Use user's field name 'max_score'
		if self.score and self.max_score:
			self.percentage = flt(self.score) / flt(self.max_score) * 100

	def validate_score(self):
		"""Validate that score doesn't exceed max score"""
		# Use user's field name 'max_score'
		if self.max_score and flt(self.score) > flt(self.max_score):
			frappe.throw("Score cannot be greater than Max Score")
		
		if flt(self.score) < 0:
			frappe.throw("Score cannot be negative")

	def on_submit(self):
		"""Trigger term calculation if this is the last result for the term"""
		# This will be handled by server script for better flexibility
		pass

	def on_cancel(self):
		"""Recalculate term results when a result is cancelled"""
		# This will be handled by server script for better flexibility
		pass


def calculate_term_results(semester, academic_year, student_group=None, submit_results=True):
	"""
	Calculate term results for all students in a semester
	This function will be called by server script or manually
	"""
	# Get all students in the semester using user's field names
	filters = {
		"semester": semester,  # user's field name for academic term
		"academic_year": academic_year,
		"docstatus": 1
	}
	
	if student_group:
		filters["student_group"] = student_group
	
	# Get all submitted results for the semester
	results = frappe.get_all("Student Term Subject Result", 
		filters=filters,
		fields=["student", "student_group", "subject", "score", "max_score"]
	)
	
	if not results:
		frappe.msgprint("No submitted results found for the specified term")
		return
	
	# Group results by student and student group
	student_data = {}
	for result in results:
		# Get student name separately since it's not in the result
		student_name = frappe.db.get_value("Student", result.student, "student_name") or result.student
		
		key = (result.student, result.student_group)
		if key not in student_data:
			student_data[key] = {
				"student": result.student,
				"student_name": student_name,
				"student_group": result.student_group,
				"subjects": {}
			}
		
		if result.subject not in student_data[key]["subjects"]:
			student_data[key]["subjects"][result.subject] = {
				"total_score": 0,
				"total_max_score": 0
			}
		
		student_data[key]["subjects"][result.subject]["total_score"] += result.score
		student_data[key]["subjects"][result.subject]["total_max_score"] += result.max_score
	
	# Group students by student_group for proper ranking calculation
	groups = {}
	for (student, student_group), data in student_data.items():
		if student_group not in groups:
			groups[student_group] = []
		groups[student_group].append(data)
	
	# Process each student group together for proper ranking
	for group_name, group_students in groups.items():
		# Create all term reports in draft mode first
		draft_reports = []
		for data in group_students:
			draft_report = create_term_report_draft(
				student=data["student"],
				student_name=data["student_name"],
				academic_year=academic_year,
				academic_term=semester,  # pass semester as academic_term to maintain compatibility
				student_group=data["student_group"],
				subjects_data=data["subjects"]
			)
			draft_reports.append(draft_report)
		
		# Calculate rankings for the entire group
		calculate_and_set_term_ranks_for_group(academic_year, semester, group_name)
		
		# Submit all reports with rankings already set (if requested)
		if submit_results:
			for report in draft_reports:
				report.reload()
				report.submit()
	
	if submit_results:
		frappe.msgprint(f"Term results calculated and submitted for {len(student_data)} students")
	else:
		frappe.msgprint(f"Term results calculated and saved as drafts for {len(student_data)} students")


def create_term_report_draft(student, student_name, academic_year, academic_term, student_group, subjects_data):
	"""
	Create a draft term report for a student (without submitting)
	"""
	# Check if report already exists
	existing = frappe.db.exists("Student Term Report", {
		"student": student,
		"academic_year": academic_year,
		"academic_term": academic_term,
		"student_group": student_group
	})

	if existing:
		doc = frappe.get_doc("Student Term Report", existing)
		# Cancel if submitted to allow updates
		if doc.docstatus == 1:
			doc.cancel()
	else:
		doc = frappe.new_doc("Student Term Report")
		doc.student = student
		doc.student_name = student_name
		doc.academic_year = academic_year
		doc.academic_term = academic_term
		doc.student_group = student_group

	# Clear existing course summary
	doc.course_summary = []

	# Add course summary data
	total_percentage = 0
	subject_count = 0

	for subject, data in subjects_data.items():
		if data["total_max_score"] > 0:
			percentage = (data["total_score"] / data["total_max_score"]) * 100
			total_percentage += percentage
			subject_count += 1

			doc.append("course_summary", {
				"course": subject,
				"total_score_for_term": data["total_score"],
				"total_maximum_score": data["total_max_score"],
				"percentage": percentage
			})

	# Calculate term average
	if subject_count > 0:
		doc.term_average = total_percentage / subject_count

	# Save as draft only
	doc.save()
	return doc


def calculate_and_set_term_ranks_for_group(academic_year, academic_term, student_group):
	"""Calculate and set ranks for all draft term reports in a group"""
	from education.education.doctype.student_term_report.student_term_report import calculate_and_set_term_ranks
	calculate_and_set_term_ranks(academic_year, academic_term, student_group)


def calculate_year_results(academic_year, student_group=None, submit_results=True):
	"""
	Calculate year results by averaging term results
	This function will be called when academic year is completed
	"""
	# Get all term reports for the academic year
	filters = {
		"academic_year": academic_year,
		"docstatus": 1
	}
	
	if student_group:
		filters["student_group"] = student_group
	
	term_reports = frappe.get_all("Student Term Report",
		filters=filters,
		fields=["student", "student_name", "student_group", "term_average"]
	)
	
	if not term_reports:
		frappe.msgprint("No term reports found for the specified academic year")
		return
	
	# Group by student and calculate year average
	student_data = {}
	for report in term_reports:
		key = (report.student, report.student_group)
		if key not in student_data:
			student_data[key] = {
				"student": report.student,
				"student_name": report.student_name,
				"student_group": report.student_group,
				"term_averages": []
			}
		student_data[key]["term_averages"].append(report.term_average)
	
	# Group students by student_group for proper ranking calculation
	groups = {}
	for (student, student_group), data in student_data.items():
		if student_group not in groups:
			groups[student_group] = []
		
		year_average = sum(data["term_averages"]) / len(data["term_averages"])
		data["year_average"] = year_average
		groups[student_group].append(data)
	
	# Process each student group together for proper ranking
	for group_name, group_students in groups.items():
		# Create all year reports in draft mode first
		draft_reports = []
		for data in group_students:
			draft_report = create_year_report_draft(
				student=data["student"],
				student_name=data["student_name"],
				academic_year=academic_year,
				student_group=data["student_group"],
				year_average=data["year_average"]
			)
			draft_reports.append(draft_report)
		
		# Calculate rankings for the entire group
		calculate_and_set_year_ranks_for_group(academic_year, group_name)
		
		# Submit all reports with rankings already set (if requested)
		if submit_results:
			for report in draft_reports:
				report.reload()
				report.submit()
	
	if submit_results:
		frappe.msgprint(f"Year results calculated and submitted for {len(student_data)} students")
	else:
		frappe.msgprint(f"Year results calculated and saved as drafts for {len(student_data)} students")


def create_year_report_draft(student, student_name, academic_year, student_group, year_average):
	"""
	Create a draft year report for a student (without submitting)
	"""
	from education.education.doctype.student_year_report.student_year_report import calculate_course_summaries

	# Check if report already exists
	existing = frappe.db.exists("Student Year Report", {
		"student": student,
		"academic_year": academic_year,
		"student_group": student_group
	})

	if existing:
		doc = frappe.get_doc("Student Year Report", existing)
		# Cancel if submitted to allow updates
		if doc.docstatus == 1:
			doc.cancel()
	else:
		doc = frappe.new_doc("Student Year Report")
		doc.student = student
		doc.student_name = student_name
		doc.academic_year = academic_year
		doc.student_group = student_group

	# Set year average
	doc.year_average = year_average

	# Calculate course year summary (this populates the child table)
	calculate_course_summaries(doc)

	# Save as draft only
	doc.save()
	return doc


def calculate_and_set_year_ranks_for_group(academic_year, student_group):
	"""Calculate and set ranks for all draft year reports in a group"""
	from education.education.doctype.student_year_report.student_year_report import calculate_and_set_year_ranks
	calculate_and_set_year_ranks(academic_year, student_group) 