# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.email.doctype.email_group.email_group import add_subscribers
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, getdate
from frappe.utils.dateutils import get_dates_from_timegrain


def get_course(program):
	"""Return list of courses for a particular program
	:param program: Program
	"""
	courses = frappe.db.sql(
		"""select course, course_name from `tabProgram Course` where parent=%s""",
		(program),
		as_dict=1,
	)
	return courses


@frappe.whitelist()
def enroll_student(source_name):
	"""Creates a Student Record and returns a Program Enrollment.

	:param source_name: Student Applicant.
	"""
	frappe.publish_realtime(
		"enroll_student_progress", {"progress": [1, 4]}, user=frappe.session.user
	)
	student = get_mapped_doc(
		"Student Applicant",
		source_name,
		{
			"Student Applicant": {
				"doctype": "Student",
				"field_map": {
					"name": "student_applicant",
				},
			}
		},
		ignore_permissions=True,
	)
	student.save()

	student_applicant = frappe.db.get_value(
		"Student Applicant",
		source_name,
		["student_category", "program", "academic_year"],
		as_dict=True,
	)
	program_enrollment = frappe.new_doc("Program Enrollment")
	program_enrollment.student = student.name
	program_enrollment.student_category = student_applicant.student_category
	program_enrollment.student_name = student.student_name
	program_enrollment.program = student_applicant.program
	program_enrollment.academic_year = student_applicant.academic_year
	program_enrollment.save()

	frappe.publish_realtime(
		"enroll_student_progress", {"progress": [2, 4]}, user=frappe.session.user
	)
	return program_enrollment


@frappe.whitelist()
def check_attendance_records_exist(course_schedule=None, student_group=None, date=None):
	"""Check if Attendance Records are made against the specified Course Schedule or Student Group for given date.

	:param course_schedule: Course Schedule.
	:param student_group: Student Group.
	:param date: Date.
	"""
	if course_schedule:
		return frappe.get_list(
			"Student Attendance", filters={"course_schedule": course_schedule}
		)
	else:
		return frappe.get_list(
			"Student Attendance", filters={"student_group": student_group, "date": date}
		)


@frappe.whitelist()
def mark_attendance(
	students_present, students_absent, course_schedule=None, student_group=None, date=None
):
	"""Creates Multiple Attendance Records.

	:param students_present: Students Present JSON.
	:param students_absent: Students Absent JSON.
	:param course_schedule: Course Schedule.
	:param student_group: Student Group.
	:param date: Date.
	"""
	if student_group:
		academic_year = frappe.db.get_value("Student Group", student_group, "academic_year")
		if academic_year:
			year_start_date, year_end_date = frappe.db.get_value(
				"Academic Year", academic_year, ["year_start_date", "year_end_date"]
			)
			if getdate(date) < getdate(year_start_date) or getdate(date) > getdate(
				year_end_date
			):
				frappe.throw(
					_("Attendance cannot be marked outside of Academic Year {0}").format(academic_year)
				)

	present = json.loads(students_present)
	absent = json.loads(students_absent)

	for d in present:
		make_attendance_records(
			d["student"], d["student_name"], "Present", course_schedule, student_group, date
		)

	for d in absent:
		make_attendance_records(
			d["student"], d["student_name"], "Absent", course_schedule, student_group, date
		)

	frappe.db.commit()
	frappe.msgprint(_("Attendance has been marked successfully."))


def make_attendance_records(
	student, student_name, status, course_schedule=None, student_group=None, date=None
):
	"""Creates/Update Attendance Record.

	:param student: Student.
	:param student_name: Student Name.
	:param course_schedule: Course Schedule.
	:param status: Status (Present/Absent/Leave).
	"""
	student_attendance = frappe.get_doc(
		{
			"doctype": "Student Attendance",
			"student": student,
			"course_schedule": course_schedule,
			"student_group": student_group,
			"date": date,
		}
	)
	if not student_attendance:
		student_attendance = frappe.new_doc("Student Attendance")
	student_attendance.student = student
	student_attendance.student_name = student_name
	student_attendance.course_schedule = course_schedule
	student_attendance.student_group = student_group
	student_attendance.date = date
	student_attendance.status = status
	student_attendance.save()
	student_attendance.submit()


@frappe.whitelist()
def get_student_guardians(student):
	"""Returns List of Guardians of a Student.

	:param student: Student.
	"""
	guardians = frappe.get_all(
		"Student Guardian", fields=["guardian"], filters={"parent": student}
	)
	return guardians


@frappe.whitelist()
def get_student_group_students(student_group, include_inactive=0):
	"""Returns List of student, student_name in Student Group.

	:param student_group: Student Group.
	"""
	if include_inactive:
		students = frappe.get_all(
			"Student Group Student",
			fields=["student", "student_name"],
			filters={"parent": student_group},
			order_by="group_roll_number",
		)
	else:
		students = frappe.get_all(
			"Student Group Student",
			fields=["student", "student_name"],
			filters={"parent": student_group, "active": 1},
			order_by="group_roll_number",
		)
	return students


@frappe.whitelist()
def get_fee_structure(program, academic_term=None):
	"""Returns Fee Structure.

	:param program: Program.
	:param academic_term: Academic Term.
	"""
	fee_structure = frappe.db.get_values(
		"Fee Structure",
		{"program": program, "academic_term": academic_term},
		"name",
		as_dict=True,
	)
	return fee_structure[0].name if fee_structure else None


@frappe.whitelist()
def get_fee_components(fee_structure):
	"""Returns Fee Components.

	:param fee_structure: Fee Structure.
	"""
	if fee_structure:
		fs = frappe.get_all(
			"Fee Component",
			fields=["fees_category", "description", "amount"],
			filters={"parent": fee_structure},
			order_by="idx",
		)
		return fs


@frappe.whitelist()
def get_fee_schedule(program, student_category=None):
	"""Returns Fee Schedule.

	:param program: Program.
	:param student_category: Student Category
	"""
	fs = frappe.get_all(
		"Program Fee",
		fields=["academic_term", "fee_schedule", "due_date", "amount"],
		filters={"parent": program, "student_category": student_category},
		order_by="idx",
	)
	return fs


@frappe.whitelist()
def collect_fees(fees, amt):
	paid_amount = flt(amt) + flt(frappe.db.get_value("Fees", fees, "paid_amount"))
	total_amount = flt(frappe.db.get_value("Fees", fees, "total_amount"))
	frappe.db.set_value("Fees", fees, "paid_amount", paid_amount)
	frappe.db.set_value("Fees", fees, "outstanding_amount", (total_amount - paid_amount))
	return paid_amount


@frappe.whitelist()
def get_course_schedule_events(start, end, filters=None):
	"""Returns events for Course Schedule Calendar view rendering.

	:param start: Start date-time.
	:param end: End date-time.
	:param filters: Filters (JSON).
	"""
	from frappe.desk.calendar import get_event_conditions

	conditions = get_event_conditions("Course Schedule", filters)

	data = frappe.db.sql(
		"""select name, course, color,
			timestamp(schedule_date, from_time) as from_time,
			timestamp(schedule_date, to_time) as to_time,
			room, student_group, 0 as 'allDay'
		from `tabCourse Schedule`
		where ( schedule_date between %(start)s and %(end)s )
		{conditions}""".format(
			conditions=conditions
		),
		{"start": start, "end": end},
		as_dict=True,
		update={"allDay": 0},
	)

	return data


@frappe.whitelist()
def get_assessment_criteria(course):
	"""Returns Assessmemt Criteria and their Weightage from Course Master.

	:param Course: Course
	"""
	return frappe.get_all(
		"Course Assessment Criteria",
		fields=["assessment_criteria", "weightage"],
		filters={"parent": course},
		order_by="idx",
	)


@frappe.whitelist()
def get_assessment_students(assessment_plan, student_group):
	student_list = get_student_group_students(student_group)
	for i, student in enumerate(student_list):
		result = get_result(student.student, assessment_plan)
		if result:
			student_result = {}
			for d in result.details:
				student_result.update({d.assessment_criteria: [cstr(d.score), d.grade]})
			student_result.update(
				{"total_score": [cstr(result.total_score), result.grade], "comment": result.comment}
			)
			student.update(
				{
					"assessment_details": student_result,
					"docstatus": result.docstatus,
					"name": result.name,
				}
			)
		else:
			student.update({"assessment_details": None})
	return student_list


@frappe.whitelist()
def get_assessment_details(assessment_plan):
	"""Returns Assessment Criteria  and Maximum Score from Assessment Plan Master.

	:param Assessment Plan: Assessment Plan
	"""
	return frappe.get_all(
		"Assessment Plan Criteria",
		fields=["assessment_criteria", "maximum_score", "docstatus"],
		filters={"parent": assessment_plan},
		order_by="idx",
	)


@frappe.whitelist()
def get_result(student, assessment_plan):
	"""Returns Submitted Result of given student for specified Assessment Plan

	:param Student: Student
	:param Assessment Plan: Assessment Plan
	"""
	results = frappe.get_all(
		"Assessment Result",
		filters={
			"student": student,
			"assessment_plan": assessment_plan,
			"docstatus": ("!=", 2),
		},
	)
	if results:
		return frappe.get_doc("Assessment Result", results[0])
	else:
		return None


@frappe.whitelist()
def get_grade(grading_scale, percentage):
	"""Returns Grade based on the Grading Scale and Score.

	:param Grading Scale: Grading Scale
	:param Percentage: Score Percentage Percentage
	"""
	grading_scale_intervals = {}
	if not hasattr(frappe.local, "grading_scale"):
		grading_scale = frappe.get_all(
			"Grading Scale Interval",
			fields=["grade_code", "threshold"],
			filters={"parent": grading_scale},
		)
		frappe.local.grading_scale = grading_scale
	for d in frappe.local.grading_scale:
		grading_scale_intervals.update({d.threshold: d.grade_code})
	intervals = sorted(grading_scale_intervals.keys(), key=float, reverse=True)
	for interval in intervals:
		if flt(percentage) >= interval:
			grade = grading_scale_intervals.get(interval)
			break
		else:
			grade = ""
	return grade


@frappe.whitelist()
def log_single_assessment_score(student, assessment_plan, assessment_criteria, score):
	"""Logs or updates a single score for an assessment criterion and submits the result."""
	score = flt(score) # Ensure score is a float

	# Fetch Assessment Plan details (needed for new doc or recalculations)
	plan_details = frappe.get_doc("Assessment Plan", assessment_plan)
	grading_scale = plan_details.grading_scale
	plan_criteria_details = {crit.assessment_criteria: crit.maximum_score for crit in plan_details.details}

	if not grading_scale:
		frappe.throw(_("Grading Scale not defined in Assessment Plan {0}").format(assessment_plan))

	# Find existing Assessment Result (submitted or draft)
	result_name = frappe.db.exists("Assessment Result", {"student": student, "assessment_plan": assessment_plan, "docstatus": ["!=", 2]})

	doc = None
	is_new = False

	if result_name:
		doc = frappe.get_doc("Assessment Result", result_name)
	else:
		is_new = True
		doc = frappe.new_doc("Assessment Result")
		doc.student = student
		doc.assessment_plan = assessment_plan
		doc.grading_scale = grading_scale
		# Fetch other header fields from plan if necessary
		doc.student_name = frappe.db.get_value("Student", student, "student_name")
		doc.program = plan_details.program
		doc.course = plan_details.course
		doc.academic_year = plan_details.academic_year
		doc.academic_term = plan_details.academic_term
		doc.student_group = plan_details.student_group
		doc.assessment_group = plan_details.assessment_group
		doc.maximum_score = plan_details.maximum_assessment_score # Total max score

		# Populate details table with all criteria from the plan
		for criteria_name, max_score in plan_criteria_details.items():
			doc.append("details", {
				"assessment_criteria": criteria_name,
				"maximum_score": max_score,
				"score": 0, # Default score
				"grade": ""
			})

	# Find the specific detail row and update score/grade
	updated_detail_grade = ""
	found_detail = False
	for detail in doc.details:
		if detail.assessment_criteria == assessment_criteria:
			if score > detail.maximum_score:
				frappe.throw(_("Score {0} cannot be greater than Maximum Score {1} for {2}").format(
					score, detail.maximum_score, assessment_criteria))
			detail.score = score
			detail.grade = get_grade(grading_scale, (flt(detail.score) / detail.maximum_score) * 100 if detail.maximum_score else 0)
			updated_detail_grade = detail.grade
			found_detail = True
			break

	if not found_detail and not is_new:
		# Criteria might have been added to the plan after the result was created
		# Add the new criteria row
		max_score = plan_criteria_details.get(assessment_criteria)
		if max_score is not None:
			grade = get_grade(grading_scale, (flt(score) / max_score) * 100 if max_score else 0)
			doc.append("details", {
				"assessment_criteria": assessment_criteria,
				"maximum_score": max_score,
				"score": score,
				"grade": grade
			})
			updated_detail_grade = grade
		else:
			frappe.log_error(f"Assessment Criteria '{assessment_criteria}' not found in plan '{assessment_plan}' details.", "log_single_assessment_score")
			# Decide how to handle - maybe throw error or just log

	# Recalculate total score and overall grade for the parent document
	total_score = sum(flt(d.score) for d in doc.details)
	doc.total_score = total_score
	doc.grade = get_grade(grading_scale, (total_score / doc.maximum_score) * 100 if doc.maximum_score else 0)

	# Save and Submit
	try:
		if doc.docstatus == 1:
			# Use ignore_permissions to save submitted doc
			doc.save(ignore_permissions=True)
		else:
			# Save draft or new doc
			doc.save()
			# Submit if it was new or draft
			doc.submit()

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in log_single_assessment_score")
		frappe.throw(_("Error saving Assessment Result: {0}").format(str(e)))

	return {
		"name": doc.name,
		"overall_score": doc.total_score,
		"overall_grade": doc.grade,
		"detail_grade": updated_detail_grade # Grade for the specific criteria updated
	}


@frappe.whitelist()
def mark_assessment_result(assessment_plan, scores):
	student_score = json.loads(scores)
	assessment_details = []
	for criteria in student_score.get("assessment_details"):
		assessment_details.append(
			{
				"assessment_criteria": criteria,
				"score": flt(student_score["assessment_details"][criteria]),
			}
		)
	assessment_result = get_assessment_result_doc(
		student_score["student"], assessment_plan
	)
	assessment_result.update(
		{
			"student": student_score.get("student"),
			"assessment_plan": assessment_plan,
			"comment": student_score.get("comment"),
			"total_score": student_score.get("total_score"),
			"details": assessment_details,
		}
	)
	assessment_result.save()
	details = {}
	for d in assessment_result.details:
		details.update({d.assessment_criteria: d.grade})
	assessment_result_dict = {
		"name": assessment_result.name,
		"student": assessment_result.student,
		"total_score": assessment_result.total_score,
		"grade": assessment_result.grade,
		"details": details,
	}
	return assessment_result_dict


@frappe.whitelist()
def submit_assessment_results(assessment_plan, student_group):
	total_result = 0
	student_list = get_student_group_students(student_group)
	for i, student in enumerate(student_list):
		doc = get_result(student.student, assessment_plan)
		if doc and doc.docstatus == 0:
			total_result += 1
			doc.submit()
	return total_result


def get_assessment_result_doc(student, assessment_plan):
	assessment_result = frappe.get_all(
		"Assessment Result",
		filters={
			"student": student,
			"assessment_plan": assessment_plan,
			"docstatus": ("!=", 2),
		},
	)
	if assessment_result:
		doc = frappe.get_doc("Assessment Result", assessment_result[0])
		if doc.docstatus == 0:
			return doc
		elif doc.docstatus == 1:
			frappe.msgprint(_("Result already Submitted"))
			return None
	else:
		return frappe.new_doc("Assessment Result")


@frappe.whitelist()
def update_email_group(doctype, name):
	if not frappe.db.exists("Email Group", name):
		email_group = frappe.new_doc("Email Group")
		email_group.title = name
		email_group.save()
	email_list = []
	students = []
	if doctype == "Student Group":
		students = get_student_group_students(name)
	for stud in students:
		for guard in get_student_guardians(stud.student):
			email = frappe.db.get_value("Guardian", guard.guardian, "email_address")
			if email:
				email_list.append(email)
	add_subscribers(name, email_list)


@frappe.whitelist()
def get_current_enrollment(student, academic_year=None):
	current_academic_year = academic_year or frappe.defaults.get_defaults().academic_year
	if not current_academic_year:
		frappe.throw(_("Please set default Academic Year in Education Settings"))
	program_enrollment_list = frappe.db.sql(
		"""
		select
			name as program_enrollment, student_name, program, student_batch_name as student_batch,
			student_category, academic_term, academic_year
		from
			`tabProgram Enrollment`
		where
			student = %s and academic_year = %s
		order by creation""",
		(student, current_academic_year),
		as_dict=1,
	)

	if program_enrollment_list:
		return program_enrollment_list[0]
	else:
		return None


@frappe.whitelist()
def get_instructors(student_group):
	return frappe.get_all(
		"Student Group Instructor", {"parent": student_group}, pluck="instructor"
	)


@frappe.whitelist()
def get_user_info():
	if frappe.session.user == "Guest":
		frappe.throw("Authentication failed", exc=frappe.AuthenticationError)

	current_user = frappe.db.get_list(
		"User",
		fields=["name", "email", "enabled", "user_image", "full_name", "user_type"],
		filters={"name": frappe.session.user},
	)[0]
	current_user["session_user"] = True
	return current_user


@frappe.whitelist()
def get_student_info():
	email = frappe.session.user
	if email == "Administrator":
		return
	student_info = frappe.db.get_list(
		"Student",
		fields=["*"],
		filters={"user": email},
	)[0]

	current_program = get_current_enrollment(student_info.name)
	if current_program:
		student_groups = get_student_groups(student_info.name, current_program.program)
		student_info["student_groups"] = student_groups
		student_info["current_program"] = current_program
	return student_info


@frappe.whitelist()
def get_student_programs(student):
	# student = 'EDU-STU-2023-00043'
	programs = frappe.db.get_list(
		"Program Enrollment",
		fields=["program", "name"],
		filters={"docstatus": 1, "student": student},
	)
	return programs


def get_student_groups(student, program_name):
	# student = 'EDU-STU-2023-00043'

	student_group = frappe.qb.DocType("Student Group")
	student_group_students = frappe.qb.DocType("Student Group Student")

	student_group_query = (
		frappe.qb.from_(student_group)
		.inner_join(student_group_students)
		.on(student_group.name == student_group_students.parent)
		.select((student_group_students.parent).as_("label"))
		.where(student_group_students.student == student)
		.where(student_group.program == program_name)
		.run(as_dict=1)
	)

	return student_group_query


@frappe.whitelist()
def get_course_list_based_on_program(program_name):
	program = frappe.get_doc("Program", program_name)

	course_list = []

	for course in program.courses:
		course_list.append(course.course)
	return course_list


@frappe.whitelist()
def get_course_schedule_for_student(program_name, student_groups):
	student_groups = [sg.get("label") for sg in student_groups]

	schedule = frappe.db.get_list(
		"Course Schedule",
		fields=[
			"schedule_date",
			"room",
			"class_schedule_color",
			"course",
			"from_time",
			"to_time",
			"instructor",
			"title",
			"name",
		],
		filters={"program": program_name, "student_group": ["in", student_groups]},
		order_by="schedule_date asc",
	)
	return schedule


@frappe.whitelist()
def apply_leave(leave_data, program_name):
	attendance_based_on_course_schedule = frappe.db.get_single_value(
		"Education Settings", "attendance_based_on_course_schedule"
	)
	if attendance_based_on_course_schedule:
		apply_leave_based_on_course_schedule(leave_data, program_name)
	else:
		apply_leave_based_on_student_group(leave_data, program_name)


def apply_leave_based_on_course_schedule(leave_data, program_name):
	course_schedule_in_leave_period = frappe.db.get_list(
		"Course Schedule",
		fields=["name", "schedule_date"],
		filters={
			"program": program_name,
			"schedule_date": [
				"between",
				[leave_data.get("from_date"), leave_data.get("to_date")],
			],
		},
		order_by="schedule_date asc",
	)
	if not course_schedule_in_leave_period:
		frappe.throw(_("No classes found in the leave period"))
	for course_schedule in course_schedule_in_leave_period:
		# check if attendance record does not exist for the student on the course schedule
		if not frappe.db.exists(
			"Student Attendance",
			{"course_schedule": course_schedule.get("name"), "docstatus": 1},
		):
			make_attendance_records(
				leave_data.get("student"),
				leave_data.get("student_name"),
				"Leave",
				course_schedule.get("name"),
				None,
				course_schedule.get("schedule_date"),
			)


def apply_leave_based_on_student_group(leave_data, program_name):
	student_groups = get_student_groups(leave_data.get("student"), program_name)
	leave_dates = get_dates_from_timegrain(
		leave_data.get("from_date"), leave_data.get("to_date")
	)
	for student_group in student_groups:
		for leave_date in leave_dates:
			make_attendance_records(
				leave_data.get("student"),
				leave_data.get("student_name"),
				"Leave",
				None,
				student_group.get("label"),
				leave_date,
			)


@frappe.whitelist()
def get_student_invoices(student):
	student_sales_invoices = []

	sales_invoice_list = frappe.db.get_list(
		"Sales Invoice",
		filters={
			"student": student,
			"status": ["in", ["Paid", "Unpaid", "Overdue", "Partly Paid"]],
			"docstatus": 1,
		},
		fields=[
			"name",
			"status",
			"student",
			"due_date",
			"fee_schedule",
			"outstanding_amount",
			"currency",
			"grand_total",
		],
		order_by="status desc",
	)

	for si in sales_invoice_list:
		student_program_invoice_status = {}
		student_program_invoice_status["status"] = si.status
		student_program_invoice_status["program"] = get_program_from_fee_schedule(
			si.fee_schedule
		)
		symbol = get_currency_symbol(si.get("currency", "INR"))
		student_program_invoice_status["amount"] = symbol + " " + str(si.outstanding_amount)
		student_program_invoice_status["invoice"] = si.name
		if si.status == "Paid":
			student_program_invoice_status["amount"] = symbol + " " + str(si.grand_total)
			student_program_invoice_status[
				"payment_date"
			] = get_posting_date_from_payment_entry_against_sales_invoice(si.name)
			student_program_invoice_status["due_date"] = "-"
		else:
			student_program_invoice_status["due_date"] = si.due_date
			student_program_invoice_status["payment_date"] = "-"

		student_sales_invoices.append(student_program_invoice_status)

	print_format = get_fees_print_format() or "Standard"

	return {"invoices": student_sales_invoices, "print_format": print_format}


def get_currency_symbol(currency):
	return frappe.db.get_value("Currency", currency, "symbol") or currency


def get_posting_date_from_payment_entry_against_sales_invoice(sales_invoice):
	payment_entry = frappe.qb.DocType("Payment Entry")
	payment_entry_reference = frappe.qb.DocType("Payment Entry Reference")

	q = (
		frappe.qb.from_(payment_entry)
		.inner_join(payment_entry_reference)
		.on(payment_entry.name == payment_entry_reference.parent)
		.select(payment_entry.posting_date)
		.where(payment_entry_reference.reference_name == sales_invoice)
	).run(as_dict=1)

	if len(q) > 0:
		payment_date = q[0].get("posting_date")
		return payment_date


def get_fees_print_format():
	return frappe.db.get_value(
		"Property Setter",
		dict(property="default_print_format", doc_type="Sales Invoice"),
		"value",
	)


def get_program_from_fee_schedule(fee_schedule):

	program = frappe.db.get_value(
		"Fee Schedule", filters={"name": fee_schedule}, fieldname=["program"]
	)
	return program


@frappe.whitelist()
def get_school_abbr_logo():
	abbr = frappe.db.get_single_value(
		"Education Settings", "school_college_name_abbreviation"
	)
	logo = frappe.db.get_single_value("Education Settings", "school_college_logo")
	return {"name": abbr, "logo": logo}


@frappe.whitelist()
def get_student_attendance(student, student_group):
	return frappe.db.get_list(
		"Student Attendance",
		filters={"student": student, "student_group": student_group, "docstatus": 1},
		fields=["date", "status", "name"],
	)

def _get_behavioral_flags(student_email):
        """Get behavioral flags counts using SQL"""
        flags = frappe.db.sql("""
                SELECT
                        COUNT(CASE WHEN late = 1 THEN 1 END) as late,
                        COUNT(CASE WHEN breaking_rules = 1 THEN 1 END) as breaking_rules,
                        COUNT(CASE WHEN fight = 1 THEN 1 END) as fight,
                        COUNT(CASE WHEN sick = 1 THEN 1 END) as sick,
                        COUNT(CASE WHEN incomplete_school_items = 1 THEN 1 END) as incomplete_school_items,
                        COUNT(CASE WHEN homework_not_done = 1 THEN 1 END) as homework_not_done,
                        COUNT(*) as total_evaluations
                FROM `tabStudent Evaluation`
                WHERE students = %s
        """, student_email, as_dict=1)

        result = flags[0] if flags else {}

        # Convert None values to 0
        for key in result:
                if result[key] is None:
                        result[key] = 0

        frappe.logger().debug(f"Behavioral flags result: {result}")
        return result


@frappe.whitelist()
def get_student_evaluation(student_email):
        """Fetches and formats student evaluation data for charts"""
        try:
                # Get evaluations for the student
                evaluations = frappe.db.sql("""
                        SELECT
                                name, student_group, review_date,
                                homework, participation, tests, proficiency,
                                attendance, discipline, communicationpeer_relationships,
                                hygiene, extracurricular, sports,
                                maths, science, speaking_and_communication_skills,
                                grammar_and_vocabulary, writing, reading,
                                achievements,
                                late, breaking_rules, fight, sick,
                                incomplete_school_items, homework_not_done
                        FROM `tabStudent Evaluation`
                        WHERE students = %s
                        ORDER BY review_date DESC
                """, student_email, as_dict=1)

                if not evaluations:
                        return _get_empty_response()

                # Get behavioral flags
                behavioral_flags = _get_behavioral_flags(student_email)
                frappe.logger().debug(f"Behavioral flags before adding to result: {behavioral_flags}")

                # Calculate core metrics averages (excluding zero values)
                core_metrics = {
                        'homework': _calculate_metric_average([e.homework for e in evaluations]),
                        'participation': _calculate_metric_average([e.participation for e in evaluations]),
                        'tests': _calculate_metric_average([e.tests for e in evaluations]),
                        'proficiency': _calculate_metric_average([e.proficiency for e in evaluations])
                }

                # Prepare chart data
                labels = ["Homework", "Class Participation", "Test Scores", "Subject Proficiency"]
                values = [core_metrics[m] for m in ['homework', 'participation', 'tests', 'proficiency']]

                # Calculate overall average
                valid_values = [v for v in values if v is not None and v > 0]
                overall_average = sum(valid_values) / len(valid_values) if valid_values else 0

                # Get latest evaluation for metadata
                latest = evaluations[0] if evaluations else None

                result = {
                        "labels": labels,
                        "values": values,
                        "evaluations": evaluations,
                        "average": overall_average,
                        "metadata": {
                                "student_group": latest.get("student_group") if latest else "",
                                "total_evaluations": behavioral_flags.get('total_evaluations', 0)
                        },
                        "flags": behavioral_flags,
                        "analysis": {
                                "academic": {
                                        "maths": _calculate_metric_average([e.maths for e in evaluations]),
                                        "science": _calculate_metric_average([e.science for e in evaluations]),
                                        "writing": _calculate_metric_average([e.writing for e in evaluations]),
                                        "reading": _calculate_metric_average([e.reading for e in evaluations])
                                },
                                "communication": {
                                        "speaking": _calculate_metric_average([e.speaking_and_communication_skills for e in evaluations]),
                                        "grammar": _calculate_metric_average([e.grammar_and_vocabulary for e in evaluations]),
                                        "peer_relations": _calculate_metric_average([e.communicationpeer_relationships for e in evaluations])
                                },
                                "behavioral": {
                                        "attendance": _calculate_metric_average([e.attendance for e in evaluations]),
                                        "discipline": _calculate_metric_average([e.discipline for e in evaluations]),
                                        "hygiene": _calculate_metric_average([e.hygiene for e in evaluations]),
                                        "extracurricular": _calculate_metric_average([e.extracurricular for e in evaluations]),
                                        "sports": _calculate_metric_average([e.sports for e in evaluations])
                                }
                        }
                }

                frappe.logger().debug(f"Final result with flags: {result}")
                return result

        except Exception as e:
                frappe.log_error(f"Student Evaluation Error: {str(e)}")
                return _get_empty_response(error=str(e))

def _calculate_metric_average(values):
        """Helper function to calculate average excluding None and zero values"""
        valid_values = [float(v) for v in values if v is not None and v != 0]
        return sum(valid_values) / len(valid_values) if valid_values else 0

def _get_empty_response(error=None):
        """Helper function to return empty evaluation response"""
        response = {
                "labels": [],
                "values": [],
                "evaluations": [],
                "average": 0,
                "metadata": {
                        "student_group": "",
                        "total_evaluations": 0
                },
                "analysis": {
                        "academic": {},
                        "communication": {},
                        "behavioral": {},
                        "flags": {}
                }
        }
        if error:
                response["error"] = error
        return response

@frappe.whitelist()
def get_assessment_results(student, program):
    """Fetches assessment results for a given student and program."""
    try:
        results = frappe.db.sql("""
            SELECT 
                ar.name, ar.total_score, ar.maximum_score, ar.grade,
                ard.assessment_criteria, ard.score, ard.maximum_score AS detail_maximum_score, ard.grade AS detail_grade,
                ar.course, ar.academic_term
            FROM 
                `tabAssessment Result` ar
            JOIN 
                `tabAssessment Result Detail` ard ON ard.parent = ar.name
            WHERE 
                ar.student = %s AND ar.program = %s
        """, (student, program), as_dict=True)

        frappe.logger().info(f"Fetched assessment results for student {student} in program {program}: {results}")
        return results

    except Exception as e:
        frappe.log_error(f"Error fetching assessment results for student {student} in program {program}: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def get_student_group_details():
    # Get the current user's email
    student_email = frappe.session.user

    # Fetch the student record associated with the current user
    student_info = frappe.db.get_value("Student", {"user": student_email}, ["name"], as_dict=True)
    
    if not student_info:
        frappe.throw(_("Student not found"))

    # Find the student group that includes this student
    student_group_name = frappe.db.get_value("Student Group Student", {"student": student_info.name}, "parent")
    
    if not student_group_name:
        frappe.throw(_("Student group not found"))

    # Fetch the student group document
    student_group = frappe.get_doc("Student Group", student_group_name)
    
    # Extract instructor details
    instructors = [{"name": inst.name, "instructor_name": inst.instructor_name} for inst in student_group.instructors]

    return {
        "student_group_name": student_group.student_group_name,
        "instructors": instructors
    }

@frappe.whitelist(allow_guest=True)
def submit_teacher_evaluation(data=None):
    try:
        if not data:
            frappe.throw(_("No data received"))

        # Parse the incoming data
        evaluation_data = frappe.parse_json(data)
        
        # Get current user if reviewer is not provided
        reviewer = evaluation_data.get("reviewer") or frappe.session.user
        instructor = evaluation_data.get("instructors")

        if not instructor:
            frappe.throw(_("No instructor selected"))
        
        # Validate rating fields are between 0 and 1
        rating_fields = ['respect', 'exams', 'communication_skill', 'followup', 'homework', 'knowledge']
        for field in rating_fields:
            value = evaluation_data.get(field, 0)
            if not isinstance(value, (int, float)):
                frappe.throw(_(f"{field.replace('_', ' ').title()} must be a number"))
            if value < 0 or value > 1:
                frappe.throw(_(f"{field.replace('_', ' ').title()} rating must be between 0 and 1"))
        
        # Check for existing review with better error handling
        existing_review = frappe.db.exists("Teacher Evaluation", {
            "reviewer": reviewer,
            "instructors": instructor
        })
        
        if existing_review:
            review_date = frappe.db.get_value("Teacher Evaluation", existing_review, "review_date")
            frappe.throw(_("You have already submitted an evaluation for this instructor on {0}").format(
                frappe.format(review_date, {'fieldtype': 'Date'})
            ))

        # Create a new Teacher Evaluation document
        evaluation = frappe.get_doc({
            "doctype": "Teacher Evaluation",
            "student_group": evaluation_data.get("student_group"),
            "instructors": instructor,
            "review_date": evaluation_data.get("review_date") or frappe.utils.today(),
            "respect": float(evaluation_data.get("respect", 0)),
            "exams": float(evaluation_data.get("exams", 0)),
            "communication_skill": float(evaluation_data.get("communication_skill", 0)),
            "followup": float(evaluation_data.get("followup", 0)),
            "homework": float(evaluation_data.get("homework", 0)),
            "knowledge": float(evaluation_data.get("knowledge", 0)),
            "feedback": evaluation_data.get("feedback", ""),
            "reviewer": reviewer
        })

        # Insert and save with proper error handling
        try:
            evaluation.insert(ignore_permissions=True)
            evaluation.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Failed to save evaluation: {str(e)}")
            frappe.throw(_("Failed to save evaluation. Please try again."))

        return {
            "message": _("Evaluation submitted successfully."),
            "evaluation": {
                "name": evaluation.name,
                "review_date": evaluation.review_date,
                "instructor": evaluation.instructors
            }
        }

    except frappe.ValidationError as e:
        # Pass validation errors directly to frontend
        raise e
    except Exception as e:
        frappe.log_error(f"Error submitting evaluation: {str(e)}")
        frappe.throw(_("An unexpected error occurred. Please try again."))

@frappe.whitelist()
def get_existing_teacher_reviews(student=None):
    """Returns a list of teachers already reviewed by the student."""
    try:
        if not student:
            student = frappe.session.user

        reviews = frappe.get_all(
            "Teacher Evaluation",
            filters={"reviewer": student},
            fields=["instructors", "name", "review_date", "respect", "exams", 
                   "communication_skill", "followup", "homework", "knowledge", "feedback"],
            order_by="review_date desc"
        )
        
        # Format dates for frontend
        for review in reviews:
            review.review_date = frappe.format(review.review_date, {'fieldtype': 'Date'})
        
        return {
            "reviewed_teachers": [r.instructors for r in reviews],
            "review_details": reviews,
            "total_reviews": len(reviews)
        }

    except Exception as e:
        frappe.log_error(f"Error fetching teacher reviews: {str(e)}")
        frappe.throw(_("Failed to fetch existing reviews"))


