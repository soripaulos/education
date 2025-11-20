import frappe
from frappe import _


ALLOWED_RESULT_USERS = {"wubet", "sori"}


def ensure_result_page_access():
	"""Ensure user has permission to access the result entry page"""
	user = frappe.session.user
	
	# Check if user is logged in
	if user == "Guest":
		frappe.throw(
			_("Please log in to access the Student Result Entry page."), 
			frappe.PermissionError
		)
	
	# Check if user is authorized
	username = (frappe.db.get_value("User", user, "username") or "").lower()
	email = (user or "").lower()
	allowed = {u.lower() for u in ALLOWED_RESULT_USERS}
	
	if email == "administrator":
		return  # Administrator always has access
	
	if email not in allowed and username not in allowed:
		frappe.throw(
			_("You are not authorized to access this page."), 
			frappe.PermissionError
		)


def get_context(context):
	"""Set up context for the wubet page template"""
	ensure_result_page_access()
	
	# Set page metadata
	context.title = _("Student Result Entry")
	context.no_cache = 1
	
	# Default values
	default_academic_year = "2018 E.C."
	
	# Semester options
	semester_options = [
		{"label": "2018 E.C. (First Semester)", "value": "2018 E.C. (First Semester)"},
		{"label": "2018 E.C. (Second Semester)", "value": "2018 E.C. (Second Semester)"},
	]
	
	# Exam options with their maximum scores
	exam_options = [
		{"label": "First Test", "value": "First Test", "max_score": 15},
		{"label": "Second Test", "value": "Second Test", "max_score": 15},
		{"label": "Mid Exam", "value": "Mid Exam", "max_score": 20},
		{"label": "Final Exam", "value": "Final Exam", "max_score": 50},
	]
	
	# Fetch student groups
	student_groups = frappe.get_all(
		"Student Group",
		fields=["name", "student_group_name", "program"],
		order_by="student_group_name",
	)
	
	# Fetch all subjects/courses
	subjects = frappe.get_all(
		"Course",
		fields=["name", "course_name"],
		order_by="course_name",
	)
	
	# Fetch all programs/grades
	grades = frappe.get_all(
		"Program",
		fields=["name", "program_name"],
		order_by="program_name",
	)
	
	# Build program-to-courses mapping
	program_course_rows = frappe.get_all(
		"Program Course",
		filters={"parenttype": "Program"},
		fields=["parent", "course", "course_name", "idx"],
		order_by="parent asc, idx asc",
	)
	
	program_courses = {}
	for row in program_course_rows:
		program_courses.setdefault(row.parent, []).append({
			"course": row.course,
			"course_name": row.course_name or row.course
		})
	
	# Prepare boot data for the frontend
	context.wubet_boot = frappe.as_json({
		"student_groups": student_groups,
		"subjects": subjects,
		"grades": grades,
		"default_academic_year": default_academic_year,
		"semesters": semester_options,
		"exam_options": exam_options,
		"program_courses": program_courses,
	})
	
	# Ensure CSRF token is available
	# Frappe's get_csrf_token will create one if it doesn't exist
	from frappe.sessions import get_csrf_token
	context.csrf_token = get_csrf_token()
	
	return context
