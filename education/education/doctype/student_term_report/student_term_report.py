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

		# Calculate rank with proper tie handling
		ranks = {}
		current_rank = 1
		prev_average = None
		
		for i, report in enumerate(reports):
			current_average = flt(report.term_average)
			
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
			frappe.db.set_value("Student Term Report", name, "rank_in_group", rank, update_modified=False)
		frappe.db.commit()


def calculate_and_set_term_ranks(academic_year, academic_term, student_group):
	"""Calculate and set ranks for all term reports in a group before submission"""
	reports = frappe.get_all("Student Term Report",
		filters={
			"student_group": student_group,
			"academic_term": academic_term,
			"academic_year": academic_year,
			"docstatus": 0  # Only draft documents
		},
		fields=["name", "term_average"],
		order_by="term_average desc"
	)

	if not reports:
		return

	# Calculate rank with proper tie handling
	ranks = {}
	current_rank = 1
	prev_average = None
	
	for i, report in enumerate(reports):
		current_average = flt(report.term_average)
		
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
		frappe.db.set_value("Student Term Report", name, "rank_in_group", rank, update_modified=False)
	frappe.db.commit() 