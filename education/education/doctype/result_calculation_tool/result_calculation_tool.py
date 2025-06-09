# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ResultCalculationTool(Document):
	pass


@frappe.whitelist()
def calculate_results(calculation_type, academic_year, semester=None, student_group=None):
	"""
	Calculate term or year results based on parameters
	Updated to use user's field names: semester instead of academic_term
	"""
	try:
		if calculation_type == "Term Results":
			if not semester:
				frappe.throw("Semester is required for Term Results calculation")
			
			from education.education.doctype.student_term_subject_result.student_term_subject_result import calculate_term_results
			calculate_term_results(semester, academic_year, student_group)
			
		elif calculation_type == "Year Results":
			from education.education.doctype.student_term_subject_result.student_term_subject_result import calculate_year_results
			calculate_year_results(academic_year, student_group)
		
		else:
			frappe.throw("Invalid calculation type")
			
		frappe.db.commit()
		return {"status": "success", "message": "Calculation completed successfully"}
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Result calculation failed: {str(e)}")
		return {"status": "error", "message": str(e)} 