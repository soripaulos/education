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
		self.queue_action(
			"calculate_rank_for_group",
			student_group=self.student_group,
			academic_term=self.academic_term,
			academic_year=self.academic_year,
		)

	def calculate_rank_for_group(self, student_group, academic_term, academic_year):
		"""Calculate rank for all students in the group"""
		reports = frappe.get_all("Student Term Report",
			filters={
				"student_group": student_group,
				"academic_term": academic_term,
				"academic_year": academic_year,
				"docstatus": 1
			},
			fields=["name", "term_average"],
			order_by="term_average desc"
		)

		if not reports:
			return

		# Calculate rank with tie handling
		ranks = {}
		current_rank = 0
		prev_average = -1
		
		for i, report in enumerate(reports):
			if flt(report.term_average) < flt(prev_average):
				current_rank = i + 1
			elif flt(report.term_average) == flt(prev_average):
				# Tied, so same rank as previous
				pass
			else:
				# New rank
				current_rank = i + 1
		
			ranks[report.name] = current_rank
			prev_average = report.term_average

		# Update all reports in the group
		for name, rank in ranks.items():
			frappe.db.set_value("Student Term Report", name, "rank_in_group", rank, update_modified=False)
		frappe.db.commit()


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