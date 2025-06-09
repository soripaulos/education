# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class StudentTermReport(Document):
	def validate(self):
		if self.student:
			self.student_name = frappe.db.get_value("Student", self.student, "student_name")
		self.calculate_term_average()

	def calculate_term_average(self):
		"""Calculate term average from course summary"""
		if self.course_summary:
			total_score = sum([flt(row.total_score_for_term) for row in self.course_summary])
			total_subjects = len(self.course_summary)
			if total_subjects > 0:
				self.term_average = total_score / total_subjects

	def on_submit(self):
		"""Calculate rank after submission"""
		self.calculate_rank()

	def calculate_rank(self):
		"""Calculate rank within student group"""
		if not self.term_average or not self.student_group:
			return

		# Get all submitted term reports for the same group, term, and year
		reports = frappe.get_all("Student Term Report", 
			filters={
				"student_group": self.student_group,
				"academic_term": self.academic_term,
				"academic_year": self.academic_year,
				"docstatus": 1
			},
			fields=["name", "term_average"],
			order_by="term_average desc"
		)

		# Calculate rank with tie handling
		rank = 1
		prev_average = None
		actual_position = 1

		for report in reports:
			if prev_average is not None and flt(report.term_average) < flt(prev_average):
				rank = actual_position
			
			if report.name == self.name:
				self.rank_in_group = rank
				frappe.db.set_value("Student Term Report", self.name, "rank_in_group", rank)
				break
			
			prev_average = report.term_average
			actual_position += 1


def create_or_update_term_report(student, student_name, academic_year, academic_term, student_group, subjects_data):
	"""
	Create or update a term report for a student
	subjects_data: dict with subject as key and {total_score, total_max_score} as value
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

	# Save and submit
	doc.save()
	doc.submit()

	return doc 