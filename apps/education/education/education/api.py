import frappe

@frappe.whitelist()
def create_and_submit_term_subject_result(roster_plan, student, score):
	"""
	Creates and submits a Student Term Subject Result document based on a Roster Plan.
	"""
	try:
		# Fetch details from the provided Roster Plan
		plan = frappe.get_doc("Roster Plan", roster_plan)

		# Create a new Student Term Subject Result document
		doc = frappe.new_doc("Student Term Subject Result")
		doc.roster_plan = roster_plan
		doc.student = student
		doc.score = float(score)
		
		# Map fields from the Roster Plan to the new document
		doc.academic_year = plan.academic_year
		doc.academic_term = plan.academic_term
		doc.grade = plan.grade
		doc.subject = plan.subject
		doc.assessment_criteria = plan.assessment_criteria
		doc.examiner = plan.examiner
		doc.max_score = plan.maximum_assessment_score

		# Fetch and set the student's name
		doc.student_name = frappe.db.get_value("Student", student, "student_name")

		# Insert the document (with permissions ignored) and submit it
		doc.insert(ignore_permissions=True)
		doc.submit()
		
		# Return the created document as a dictionary
		return doc.as_dict()

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create Student Term Subject Result API Error")
		frappe.throw(str(e)) 