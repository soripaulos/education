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


def calculate_term_results(semester, academic_year, student_group=None):
	"""
	Calculate term results for all students in a semester
	This function will be called by server script or manually
	"""
	from education.education.doctype.student_term_report.student_term_report import create_or_update_term_report
	
	# Get all students in the semester using user's field names
	filters = {
		"semester": semester,  # user's field name for academic term
		"academic_year": academic_year,
		"docstatus": 1
	}
	
	if student_group:
		filters["section"] = student_group  # user's field name for student group
	
	# Get all submitted results for the semester
	results = frappe.get_all("Student Term Subject Result", 
		filters=filters,
		fields=["student", "section", "subject", "score", "max_score"]
	)
	
	if not results:
		frappe.msgprint("No submitted results found for the specified term")
		return
	
	# Group results by student and student group
	student_data = {}
	for result in results:
		# Get student name separately since it's not in the result
		student_name = frappe.db.get_value("Student", result.student, "student_name") or result.student
		
		key = (result.student, result.section)  # using user's field name 'section'
		if key not in student_data:
			student_data[key] = {
				"student": result.student,
				"student_name": student_name,
				"student_group": result.section,  # user uses 'section' for student group
				"subjects": {}
			}
		
		if result.subject not in student_data[key]["subjects"]:
			student_data[key]["subjects"][result.subject] = {
				"total_score": 0,
				"total_max_score": 0
			}
		
		student_data[key]["subjects"][result.subject]["total_score"] += result.score
		student_data[key]["subjects"][result.subject]["total_max_score"] += result.max_score  # user's field name
	
	# Calculate term averages and create/update term reports
	for (student, student_group), data in student_data.items():
		create_or_update_term_report(
			student=student,
			student_name=data["student_name"],
			academic_year=academic_year,
			academic_term=semester,  # pass semester as academic_term to maintain compatibility
			student_group=student_group,
			subjects_data=data["subjects"]
		)
	
	frappe.msgprint(f"Term results calculated for {len(student_data)} students")


def calculate_year_results(academic_year, student_group=None):
	"""
	Calculate year results by averaging term results
	This function will be called when academic year is completed
	"""
	from education.education.doctype.student_year_report.student_year_report import create_or_update_year_report
	
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
	
	# Create/update year reports
	for (student, student_group), data in student_data.items():
		year_average = sum(data["term_averages"]) / len(data["term_averages"])
		create_or_update_year_report(
			student=student,
			student_name=data["student_name"],
			academic_year=academic_year,
			student_group=student_group,
			year_average=year_average
		)
	
	frappe.msgprint(f"Year results calculated for {len(student_data)} students") 