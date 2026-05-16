# Copyright (c) 2026, Makkobilli School
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ReportCardGenerator(Document):
	pass


@frappe.whitelist()
def get_academic_years():
	"""Return all Academic Year options."""
	return frappe.get_all(
		"Academic Year",
		fields=["name", "year_start_date", "year_end_date"],
		order_by="year_start_date desc",
	)


@frappe.whitelist()
def get_student_groups(academic_year):
	"""Return student groups that have STRs for the given academic year."""
	groups = frappe.get_all(
		"Student Term Report",
		filters={"academic_year": academic_year},
		fields=["distinct student_group as name"],
	)
	return [g.name for g in groups if g.name]


@frappe.whitelist()
def get_students(student_group):
	"""Return students in a group."""
	students = frappe.get_all(
		"Student Group Student",
		filters={"parent": student_group},
		fields=["student"],
	)
	return [s.student for s in students if s.student]


def _get_grade(percentage):
	"""Return letter grade from percentage. Passing >= 60."""
	if percentage is None:
		return None
	if percentage >= 95:
		return "A+"
	elif percentage >= 90:
		return "A"
	elif percentage >= 85:
		return "B+"
	elif percentage >= 80:
		return "B"
	elif percentage >= 70:
		return "C"
	elif percentage >= 60:
		return "D"
	return "F"


def _get_promotion_decision(year_average):
	"""Return promotion decision string."""
	if year_average is None or year_average < 60:
		return "Detained"
	return "Promoted"


def generate_student_report_card(student, academic_year):
	"""
	Generate or update a Report Card for a given student + academic year.
	Reads from Student Term Report (per semester) and Student Year Report (year summary).
	"""
	# --- 1. Fetch STRs ----------------------------------------------------
	strs = frappe.get_all(
		"Student Term Report",
		filters={"student": student, "academic_year": academic_year},
		fields=[
			"name", "academic_term", "student_group", "term_average", "rank_in_group",
			"custom_first_semester_remarks", "custom_second_semester_remarks",
			"custom_final_result", "custom_director_signature",
		],
		order_by="academic_term asc",
	)

	if not strs:
		frappe.throw(f"No Student Term Reports for student {student} in {academic_year}")

	# Separate by semester
	first_str = None
	second_str = None
	for s in strs:
		term = (s.academic_term or "").lower()
		if "second" in term:
			second_str = s
		else:
			first_str = s

	# --- 2. Fetch Year Report ---------------------------------------------
	year_reports = frappe.get_all(
		"Student Year Report",
		filters={"student": student, "academic_year": academic_year},
		fields=["name", "year_average", "rank_in_group"],
	)
	year_report = year_reports[0] if year_reports else None

	# --- 3. Fetch student info --------------------------------------------
	student_doc = frappe.get_doc("Student", student)
	student_name = student_doc.student_name
	student_group_name = first_str.student_group if first_str else None

	# --- 4. Build semester rows (from STRs) --------------------------------
	semesters = []

	for str_rec in [first_str, second_str]:
		if not str_rec:
			continue

		# Courses from Course Term Summary
		courses = []
		cts_rows = frappe.get_all(
			"Course Term Summary",
			filters={"parent": str_rec.name},
			fields=["course", "total_score_for_term", "total_maximum_score", "percentage"],
		)
		for cts in cts_rows:
			courses.append({
				"course":     cts.course,
				"score":      cts.total_score_for_term,
				"maximum":    cts.total_maximum_score,
				"percentage": cts.percentage,
			})

		semesters.append({
			"academic_term":          str_rec.academic_term,
			"term_average":            str_rec.term_average,
			"rank_in_group":          str_rec.rank_in_group,
			"promotion_decision":     str_rec.custom_final_result,
			"first_semester_remarks": str_rec.custom_first_semester_remarks,
			"second_semester_remarks": str_rec.custom_second_semester_remarks,
			"courses":                courses,
		})

	# --- 5. Build year course rows (from SYR) ----------------------------
	year_courses = []
	if year_report:
		cys_rows = frappe.get_all(
			"Course Year Summary",
			filters={"parent": year_report.name},
			fields=["course", "total_year_score", "total_year_max_score", "year_average_percentage"],
		)
		for cys in cys_rows:
			year_courses.append({
				"course":                  cys.course,
				"total_year_score":        cys.total_year_score,
				"total_year_max_score":    cys.total_year_max_score,
				"year_average_percentage": cys.year_average_percentage,
			})

	# --- 6. Compute year average ------------------------------------------
	year_avg = year_report.year_average if year_report else None
	if (year_avg == 0 or year_avg is None) and year_courses:
		vals = [y.year_average_percentage for y in year_courses if y.year_average_percentage]
		year_avg = sum(vals) / len(vals) if vals else None

	# --- 7. Upsert Report Card --------------------------------------------
	existing = frappe.get_all(
		"Report Card",
		filters={"student": student, "academic_year": academic_year},
		fields=["name"],
	)

	if existing:
		rc = frappe.get_doc("Report Card", existing[0].name)
		rc.set("student_name", student_name)
		rc.set("student_group", student_group_name)
		rc.set("is_final", 1 if year_report else 0)
		rc.set("year_average", year_avg)
		rc.set("rank_in_group", year_report.rank_in_group if year_report else None)
		rc.set("semesters", semesters)
		rc.set("year_courses", year_courses)
		rc.save()
		action = "Updated"
	else:
		rc = frappe.get_doc({
			"doctype":    "Report Card",
			"naming_series": "RCR-",
			"student":       student,
			"student_name":  student_name,
			"academic_year": academic_year,
			"student_group": student_group_name,
			"is_final":      1 if year_report else 0,
			"year_average":  year_avg,
			"rank_in_group": year_report.rank_in_group if year_report else None,
			"semesters":     semesters,
			"year_courses":  year_courses,
		})
		rc.insert()
		action = "Created"

	return {"name": rc.name, "action": action}


@frappe.whitelist()
def generate_report_cards(generation_mode, academic_year, student=None, student_group=None, result_action="Save as Draft"):
	"""
	Generate Report Card doctype records for a student, group, or all students.
	Called from Report Card Generator Tool via frappe.call.
	"""
	try:
		if not academic_year:
			return {"status": "error", "message": "Academic Year is required"}
		if not generation_mode:
			return {"status": "error", "message": "Generation Mode is required"}

		# Collect students
		if generation_mode == "Single Student":
			if not student:
				return {"status": "error", "message": "Student is required for Single Student mode"}
			students = [student]
		elif generation_mode == "Student Group":
			if not student_group:
				return {"status": "error", "message": "Student Group is required for Student Group mode"}
			sg = frappe.get_doc("Student Group", student_group)
			students = [d.student for d in sg.students] if sg.students else []
		else:  # All Students
			strs = frappe.get_all(
				"Student Term Report",
				filters={"academic_year": academic_year},
				fields=["distinct student as name"],
			)
			students = [s.name for s in strs]

		if not students:
			return {"status": "error", "message": "No students found for the selected criteria"}

		generated = 0
		errors = []

		for stu in students:
			try:
				result = generate_student_report_card(stu, academic_year)
				generated += 1
			except Exception as e:
				errors.append(f"{stu}: {str(e)}")

		msg = f"Generated {generated} Report Cards."
		if errors:
			msg += f" Errors: {len(errors)}: {'; '.join(errors[:5])}"

		return {"status": "success", "message": msg, "count": generated}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Report Card Generator Error")
		return {"status": "error", "message": str(e)}