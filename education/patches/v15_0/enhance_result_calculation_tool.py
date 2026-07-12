import frappe


def execute():
	"""Install the revamped Result Calculation Tool.

	- new: Result Calculation Log (+ Entry), Result Calculation Course/Term
	- updated: Result Calculation Tool (policies, previews),
	  Course (exclude_from_result_average flag),
	  Course Term/Year Summary (excluded_from_average flag),
	  Student Year Report (partial-year tracking fields)
	"""

	# child tables first
	frappe.reload_doc("education", "doctype", "result_calculation_log_entry")
	frappe.reload_doc("education", "doctype", "result_calculation_course")
	frappe.reload_doc("education", "doctype", "result_calculation_term")
	frappe.reload_doc("education", "doctype", "course_term_summary")
	frappe.reload_doc("education", "doctype", "course_year_summary")

	# parents
	frappe.reload_doc("education", "doctype", "result_calculation_log")
	frappe.reload_doc("education", "doctype", "result_calculation_tool")
	frappe.reload_doc("education", "doctype", "course")
	frappe.reload_doc("education", "doctype", "student_term_report")
	frappe.reload_doc("education", "doctype", "student_year_report")
