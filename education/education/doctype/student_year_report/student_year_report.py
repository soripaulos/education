# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class StudentYearReport(Document):
	def validate(self):
		if self.student:
			self.student_name = frappe.db.get_value("Student", self.student, "student_name")

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

		# Calculate rank with tie handling
		ranks = {}
		current_rank = 0
		prev_average = -1
		
		for i, report in enumerate(reports):
			if flt(report.year_average) < flt(prev_average):
				current_rank = i + 1
			elif flt(report.year_average) == flt(prev_average):
				# Tied, so same rank as previous
				pass
			else:
				# New rank
				current_rank = i + 1
		
			ranks[report.name] = current_rank
			prev_average = report.year_average

		# Update all reports in the group
		for name, rank in ranks.items():
			frappe.db.set_value("Student Year Report", name, "rank_in_group", rank, update_modified=False)
		frappe.db.commit()


def create_or_update_year_report(student, student_name, academic_year, student_group, year_average):
	"""
	Create or update a year report for a student
	"""
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

	# Save and submit
	doc.save()
	doc.submit()

	return doc 