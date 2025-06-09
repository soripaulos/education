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
		self.calculate_rank()

	def calculate_rank(self):
		"""Calculate rank within student group for the year"""
		if not self.year_average or not self.student_group:
			return

		# Get all submitted year reports for the same group and year
		reports = frappe.get_all("Student Year Report", 
			filters={
				"student_group": self.student_group,
				"academic_year": self.academic_year,
				"docstatus": 1
			},
			fields=["name", "year_average"],
			order_by="year_average desc"
		)

		# Calculate rank with tie handling
		rank = 1
		prev_average = None
		actual_position = 1

		for report in reports:
			if prev_average is not None and flt(report.year_average) < flt(prev_average):
				rank = actual_position
			
			if report.name == self.name:
				self.rank_in_group = rank
				frappe.db.set_value("Student Year Report", self.name, "rank_in_group", rank)
				break
			
			prev_average = report.year_average
			actual_position += 1


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