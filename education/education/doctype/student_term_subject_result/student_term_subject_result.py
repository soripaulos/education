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
		# Always calculate percentage if max_score is set
		if self.max_score and flt(self.max_score) > 0:
			self.percentage = round(flt(self.score) / flt(self.max_score) * 100, 2)
		elif flt(self.score) == 0 and flt(self.max_score) == 0:
			self.percentage = 0
		else:
			# If max_score is 0 but score is set, set percentage to 0
			self.percentage = 0

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
	Calculate term results for all students in a semester.

	Kept for backward compatibility (server scripts / legacy API endpoints).
	Delegates to the Result Calculation Tool engine, which adds validation,
	logging, course exclusions and per-student error isolation.
	"""
	from education.education.doctype.result_calculation_tool.result_calculation_tool import (
		start_calculation,
	)

	result = start_calculation(
		{
			"calculation_type": "Term Results",
			"academic_year": academic_year,
			"semester": semester,
			"student_group": student_group,
			"result_action": "Save and Submit" if submit_results else "Save as Draft",
			"run_in_background": 0,
		}
	)
	frappe.msgprint(f"{result.get('summary')} (see Result Calculation Log {result.get('log_name')})")
	return result


def calculate_year_results(academic_year, student_group=None, submit_results=True):
	"""
	Calculate year results by averaging term results.

	Kept for backward compatibility (server scripts / legacy API endpoints).
	Delegates to the Result Calculation Tool engine, which adds validation,
	logging, missing-term policies and per-student error isolation.
	"""
	from education.education.doctype.result_calculation_tool.result_calculation_tool import (
		start_calculation,
	)

	result = start_calculation(
		{
			"calculation_type": "Year Results",
			"academic_year": academic_year,
			"student_group": student_group,
			"result_action": "Save and Submit" if submit_results else "Save as Draft",
			"run_in_background": 0,
		}
	)
	frappe.msgprint(f"{result.get('summary')} (see Result Calculation Log {result.get('log_name')})")
	return result


def update_all_percentages(commit=True):
	"""
	Update percentage field for all existing Student Term Subject Result records
	Can be called from console or via script
	
	Usage:
		bench --site [site-name] console
		>>> from education.education.doctype.student_term_subject_result.student_term_subject_result import update_all_percentages
		>>> update_all_percentages()
	"""
	import frappe
	from frappe.utils import flt
	
	print("\n" + "="*60)
	print("Updating Percentages for Student Term Subject Results")
	print("="*60 + "\n")
	
	# Get all records (including cancelled ones for completeness)
	results = frappe.get_all(
		"Student Term Subject Result",
		fields=["name", "score", "max_score", "percentage", "docstatus"],
		order_by="creation desc"
	)
	
	if not results:
		print("No records found.")
		return
	
	print(f"Found {len(results)} records to process...\n")
	
	updated_count = 0
	skipped_count = 0
	error_count = 0
	
	for result in results:
		try:
			score = flt(result.score)
			max_score = flt(result.max_score)
			old_percentage = flt(result.percentage)
			
			# Calculate new percentage
			if max_score > 0:
				new_percentage = round((score / max_score) * 100, 2)
			else:
				new_percentage = 0
			
			# Check if update is needed
			if old_percentage != new_percentage:
				# Use direct SQL update to bypass validation and avoid re-triggering
				frappe.db.sql("""
					UPDATE `tabStudent Term Subject Result`
					SET percentage = %s
					WHERE name = %s
				""", (new_percentage, result.name))
				
				updated_count += 1
				print(f"✓ Updated {result.name}: {old_percentage}% → {new_percentage}%")
			else:
				skipped_count += 1
		
		except Exception as e:
			error_count += 1
			print(f"✗ Error updating {result.name}: {str(e)}")
	
	if commit:
		frappe.db.commit()
		print(f"\n✓ Changes committed to database")
	else:
		print(f"\n⚠ Changes NOT committed (dry run)")
	
	print("\n" + "="*60)
	print("Summary:")
	print(f"  Total records: {len(results)}")
	print(f"  Updated: {updated_count}")
	print(f"  Already correct: {skipped_count}")
	print(f"  Errors: {error_count}")
	print("="*60 + "\n")
	
	return {
		"total": len(results),
		"updated": updated_count,
		"skipped": skipped_count,
		"errors": error_count
	} 