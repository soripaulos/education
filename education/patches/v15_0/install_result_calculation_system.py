import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Install the Student Result Calculation System"""
	
	# Create the new doctypes by reloading the module
	frappe.reload_doc("education", "doctype", "student_term_subject_result")
	frappe.reload_doc("education", "doctype", "result_calculation_tool")
	
	# Update existing doctypes
	frappe.reload_doc("education", "doctype", "student_term_report")
	frappe.reload_doc("education", "doctype", "student_year_report")
	frappe.reload_doc("education", "doctype", "course_term_summary")
	
	print("Student Result Calculation System installed successfully!")
	
	# Create sample data if needed
	create_sample_assessment_criteria()


def create_sample_assessment_criteria():
	"""Create sample assessment criteria if they don't exist"""
	
	sample_criteria = [
		{"name": "Midterm Exam", "maximum_score": 100},
		{"name": "Final Exam", "maximum_score": 100},
		{"name": "Assignment", "maximum_score": 50},
		{"name": "Quiz", "maximum_score": 25},
		{"name": "Project", "maximum_score": 100}
	]
	
	for criteria in sample_criteria:
		if not frappe.db.exists("Assessment Criteria", criteria["name"]):
			doc = frappe.get_doc({
				"doctype": "Assessment Criteria",
				"assessment_criteria": criteria["name"],
				"maximum_score": criteria["maximum_score"]
			})
			doc.insert(ignore_permissions=True)
			print(f"Created Assessment Criteria: {criteria['name']}") 