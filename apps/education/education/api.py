import frappe
from frappe import _

@frappe.whitelist()
def create_and_submit_term_subject_result(roster_plan, student, score):
	try:
		# Fetch details from the Roster Plan
		roster_plan_doc = frappe.get_doc("Roster Plan", roster_plan)
		
		# Basic validation
		if not roster_plan_doc:
			frappe.throw(_("Roster Plan {0} not found.").format(roster_plan))

		student_doc = frappe.get_doc("Student", student)
		if not student_doc:
			frappe.throw(_("Student {0} not found.").format(student))

		score_value = float(score)
		max_score = float(roster_plan_doc.maximum_assessment_score)

		if score_value < 0:
			frappe.throw(_("Score cannot be negative."))
		if score_value > max_score:
			frappe.throw(_("Score ({0}) cannot be greater than the maximum score ({1}).").format(score_value, max_score))

		# Check for existing record
		existing_record = frappe.db.exists("Student Term Subject Result", {
			"roster_plan": roster_plan,
			"student": student,
			"docstatus": 1
		})

		if existing_record:
			frappe.throw(_("A submitted result for this student and roster plan already exists."))

		# Create the new Student Term Subject Result document
		doc = frappe.new_doc("Student Term Subject Result")
		doc.roster_plan = roster_plan
		doc.student = student
		doc.student_name = student_doc.student_name
		doc.grade = roster_plan_doc.grade
		doc.subject = roster_plan_doc.subject
		doc.maximum_score = max_score
		doc.score = score_value
		
		doc.insert(ignore_permissions=True)
		doc.submit()
		
		return doc.as_dict()

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Create Term Subject Result API Error")
		# Re-throw with a user-friendly message
		frappe.throw(str(e))

@frappe.whitelist()
def create_and_submit_bulk_term_subject_results(results):
	if not isinstance(results, list):
		frappe.throw(_("Payload must be a list of student results."))

	success_count = 0
	failures = []

	for result in results:
		try:
			# Re-use the single submission logic for each item
			# This is efficient and avoids duplicating validation code
			create_and_submit_term_subject_result(
				roster_plan=result.get('roster_plan'),
				student=result.get('student'),
				score=result.get('score')
			)
			success_count += 1
		except Exception as e:
			# Get student name for more helpful error logging
			student_name = frappe.db.get_value("Student", result.get('student'), "student_name", cache=True)
			failures.append({
				"student": student_name or result.get('student'),
				"error": str(e)
			})
			# Log the detailed error on the server
			frappe.log_error(
				message=f"Failed to submit for student {result.get('student')}: {e}",
				title="Bulk Submission Individual Failure"
			)
	
	# Return a summary of the operation
	return {
		"success_count": success_count,
		"failure_count": len(failures),
		"failures": failures
	} 