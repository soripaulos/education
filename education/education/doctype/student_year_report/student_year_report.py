# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class StudentYearReport(Document):
	def validate(self):
		if self.student:
			self.student_name = frappe.db.get_value("Student", self.student, "student_name")
		self.calculate_year_summary_for_courses()

	def calculate_year_summary_for_courses(self):
		"""Fetch all term reports and calculate the year's summary for each course."""
		self.course_year_summary = []
		term_reports = frappe.get_all("Student Term Report",
			filters={
				"student": self.student,
				"academic_year": self.academic_year,
				"docstatus": 1
			},
			fields=["name"]
		)

		if not term_reports:
			return

		course_data = {}
		for report_info in term_reports:
			report = frappe.get_doc("Student Term Report", report_info.name)
			for summary in report.course_summary:
				course = summary.course
				if course not in course_data:
					course_data[course] = {
						"total_score": 0,
						"max_score": 0,
						"count": 0
					}
				course_data[course]["total_score"] += summary.total_score_for_term
				course_data[course]["max_score"] += summary.total_maximum_score
				course_data[course]["count"] += 1

		total_year_average = 0
		num_courses = 0
		for course, data in course_data.items():
			percentage = (data["total_score"] / data["max_score"] * 100) if data["max_score"] else 0
			self.append("course_year_summary", {
				"course": course,
				"total_year_score": data["total_score"],
				"total_year_max_score": data["max_score"],
				"year_average_percentage": percentage,
				"terms_count": data["count"]
			})
			total_year_average += percentage
			num_courses += 1
		
		if num_courses > 0:
			self.year_average = total_year_average / num_courses

	def on_submit(self):
		"""Calculate rank after submission"""
		self.queue_action(
			"calculate_rank_for_group",
			student_group=self.student_group,
			academic_year=self.academic_year,
		)

	def calculate_rank_for_group(self, student_group, academic_year):
		"""Calculate rank for all students in the group for the year"""
		reports = frappe.get_all("Student Year Report",
			filters={
				"student_group": student_group,
				"academic_year": academic_year,
				"docstatus": 1
			},
			fields=["name", "year_average"],
			order_by="year_average desc"
		)

		if not reports:
			return

		# Calculate rank with proper tie handling
		ranks = {}
		current_rank = 1
		prev_average = None
		
		for i, report in enumerate(reports):
			current_average = flt(report.year_average)
			
			if prev_average is None:
				# First student gets rank 1
				current_rank = 1
			elif current_average < prev_average:
				# Lower average gets next available rank
				current_rank = i + 1
			elif current_average == prev_average:
				# Same average gets same rank as previous
				# current_rank stays the same
				pass
			
			ranks[report.name] = current_rank
			prev_average = current_average

		# Update all reports in the group
		for name, rank in ranks.items():
			frappe.db.set_value("Student Year Report", name, "rank_in_group", rank, update_modified=False)
		frappe.db.commit()


def calculate_and_set_year_ranks(academic_year, student_group):
	"""Calculate and set ranks for all year reports in a group before submission"""
	reports = frappe.get_all("Student Year Report",
		filters={
			"student_group": student_group,
			"academic_year": academic_year,
			"docstatus": 0  # Only draft documents
		},
		fields=["name", "year_average"],
		order_by="year_average desc"
	)

	if not reports:
		return

	# Calculate rank with proper tie handling
	ranks = {}
	current_rank = 1
	prev_average = None
	
	for i, report in enumerate(reports):
		current_average = flt(report.year_average)
		
		if prev_average is None:
			# First student gets rank 1
			current_rank = 1
		elif current_average < prev_average:
			# Lower average gets next available rank
			current_rank = i + 1
		elif current_average == prev_average:
			# Same average gets same rank as previous
			# current_rank stays the same
			pass
		
		ranks[report.name] = current_rank
		prev_average = current_average

	# Update all reports in the group
	for name, rank in ranks.items():
		frappe.db.set_value("Student Year Report", name, "rank_in_group", rank, update_modified=False)
	frappe.db.commit() 