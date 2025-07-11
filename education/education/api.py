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
					"image": "image",
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
        
        # Check for existing review within the same calendar month
        from datetime import datetime
        
        review_date_str = evaluation_data.get("review_date") or frappe.utils.today()
        review_date = frappe.utils.getdate(review_date_str)
        
        # Get first and last day of the review month
        first_day_of_month = review_date.replace(day=1)
        import calendar
        _, num_days = calendar.monthrange(review_date.year, review_date.month)
        last_day_of_month = review_date.replace(day=num_days)

        existing_review = frappe.db.exists(
            "Teacher Evaluation",
            {
                "reviewer": reviewer,
                "instructors": instructor,
                "review_date": ["between", (first_day_of_month, last_day_of_month)],
            },
        )

        if existing_review:
            # Calculate next allowed review date (first day of next month)
            if review_date.month == 12:
                next_month_date = review_date.replace(year=review_date.year + 1, month=1, day=1)
            else:
                next_month_date = review_date.replace(month=review_date.month + 1, day=1)
            
            last_review_date = frappe.db.get_value("Teacher Evaluation", existing_review, "review_date")
            frappe.throw(_("You have already reviewed this instructor this month on {0}. You can submit another review after {1}.").format(
                frappe.format(last_review_date, {'fieldtype': 'Date'}),
                frappe.format(next_month_date, {'fieldtype': 'Date'})
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
    """Returns a list of teachers already reviewed by the student with monthly restrictions."""
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
        
        # Calculate monthly restrictions
        from datetime import datetime, timedelta
        import calendar
        
        current_date = datetime.now().date()
        current_month_start = current_date.replace(day=1)
        
        monthly_restrictions = {}
        current_month_reviewed = []
        
        for review in reviews:
            teacher_name = review.instructors
            review_date = frappe.utils.getdate(review.review_date)
            
            # Check if review was made in current month
            review_month_start = review_date.replace(day=1)
            if review_month_start == current_month_start:
                current_month_reviewed.append(teacher_name)
                
                # Calculate next allowed date (first day of next month)
                if current_date.month == 12:
                    next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    next_month = current_date.replace(month=current_date.month + 1, day=1)
                
                monthly_restrictions[teacher_name] = {
                    "last_reviewed_date": frappe.format(review_date, {'fieldtype': 'Date'}),
                    "next_allowed_date": frappe.format(next_month, {'fieldtype': 'Date'}),
                    "can_review": False
                }
        
        # Format dates for frontend
        for review in reviews:
            review.review_date = frappe.format(review.review_date, {'fieldtype': 'Date'})
        
        return {
            "reviewed_teachers": [r.instructors for r in reviews],
            "review_details": reviews,
            "total_reviews": len(reviews),
            "monthly_restrictions": monthly_restrictions,
            "current_month_reviewed": current_month_reviewed
        }

    except Exception as e:
        frappe.log_error(f"Error fetching teacher reviews: {str(e)}")
        frappe.throw(_("Failed to fetch existing reviews"))

@frappe.whitelist()
def get_students_for_group(student_group):
	if not student_group:
		frappe.throw(_("Please select a Student Group first"))
	return frappe.get_all(
		"Student Group Student",
		filters={"parent": student_group},
		fields=["student", "student_name"],
		order_by="student_name",
	)

@frappe.whitelist()
def create_and_submit_score(academic_year, academic_term, course, assessment_criteria, student, score, student_group):
	try:
		doc = frappe.new_doc("Student Assessment Score")
		doc.academic_year = academic_year
		doc.academic_term = academic_term
		doc.student_group = student_group
		doc.course = course
		doc.assessment_criteria = assessment_criteria
		doc.student = student
		doc.score = float(score)
		doc.insert(ignore_permissions=True)
		doc.submit()
		return doc
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Student Assessment Score API Error")
		frappe.throw(str(e))

@frappe.whitelist()
def create_and_submit_term_subject_result(data):
	data = frappe.parse_json(data)
	try:
		doc = frappe.new_doc("Student Term Subject Result")
		# Use the user's actual field names
		doc.student = data.get("student")
		doc.academic_year = data.get("academic_year")
		doc.semester = data.get("semester")  # user's field name for academic term
		doc.subject = data.get("subject")
		doc.section = data.get("section") or data.get("student_group")  # user's field name
		doc.grade = data.get("grade")
		doc.exam = data.get("exam") or data.get("assessment_criteria")  # user's field name
		doc.roster_plan = data.get("roster_plan")
		doc.score = float(data.get("score"))
		doc.max_score = float(data.get("max_score") or data.get("maximum_score"))  # user's field name
		doc.examiner = data.get("examiner") or data.get("instructor")  # user's field name
		
		doc.insert(ignore_permissions=True)
		doc.submit()
		return {"status": "success", "name": doc.name, "message": "Result submitted successfully"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Student Term Subject Result API Error")
		frappe.throw(str(e))


@frappe.whitelist()
def get_student_term_results(student, academic_year, semester=None):
	"""Get all term subject results for a student"""
	try:
		filters = {
			"student": student,
			"academic_year": academic_year,
			"docstatus": 1
		}
		
		if semester:
			filters["semester"] = semester  # user's field name
		
		results = frappe.get_all("Student Term Subject Result",
			filters=filters,
			fields=["name", "subject", "semester", "exam", 
					"score", "max_score", "percentage", "modified"],
			order_by="semester, subject"
		)
		
		return {"status": "success", "results": results}
	except Exception as e:
		frappe.log_error(f"Error fetching student term results: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_student_term_report(student, academic_year, academic_term, student_group):
	"""Get term report for a student"""
	try:
		report = frappe.db.get_value("Student Term Report", {
			"student": student,
			"academic_year": academic_year,
			"academic_term": academic_term,
			"student_group": student_group,
			"docstatus": 1
		}, ["name", "term_average", "rank_in_group"], as_dict=True)
		
		if report:
			# Get course summary
			course_summary = frappe.get_all("Course Term Summary",
				filters={"parent": report.name},
				fields=["course", "total_score_for_term", "total_maximum_score", "percentage"]
			)
			report["course_summary"] = course_summary
			
		return {"status": "success", "report": report}
	except Exception as e:
		frappe.log_error(f"Error fetching student term report: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def get_student_year_report(student, academic_year, student_group):
	"""Get year report for a student"""
	try:
		report = frappe.db.get_value("Student Year Report", {
			"student": student,
			"academic_year": academic_year,
			"student_group": student_group,
			"docstatus": 1
		}, ["name", "year_average", "rank_in_group"], as_dict=True)
		
		return {"status": "success", "report": report}
	except Exception as e:
		frappe.log_error(f"Error fetching student year report: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def trigger_term_calculation(academic_year, semester, student_group=None):
	"""Trigger term result calculation using user's field names"""
	try:
		from education.education.doctype.student_term_subject_result.student_term_subject_result import calculate_term_results
		calculate_term_results(semester, academic_year, student_group)
		return {"status": "success", "message": "Term calculation completed successfully"}
	except Exception as e:
		frappe.log_error(f"Error in term calculation: {str(e)}")
		return {"status": "error", "message": str(e)}


@frappe.whitelist()
def trigger_year_calculation(academic_year, student_group=None):
	"""Trigger year result calculation"""
	try:
		from education.education.doctype.student_term_subject_result.student_term_subject_result import calculate_year_results
		calculate_year_results(academic_year, student_group)
		return {"status": "success", "message": "Year calculation completed successfully"}
	except Exception as e:
		frappe.log_error(f"Error in year calculation: {str(e)}")
		return {"status": "error", "message": str(e)}




@frappe.whitelist()
def calculate_results(calculation_type, academic_year, semester=None, student_group=None, result_action="Save as Draft"):
	"""
	Calculate term or year results based on parameters
	Updated to use user's field names: semester instead of academic_term
	"""
	try:
		submit_results = result_action == "Save and Submit"
		
		if calculation_type == "Term Results":
			if not semester:
				frappe.throw("Semester is required for Term Results calculation")
			
			from education.education.doctype.student_term_subject_result.student_term_subject_result import calculate_term_results
			calculate_term_results(semester, academic_year, student_group, submit_results)
			
		elif calculation_type == "Year Results":
			from education.education.doctype.student_term_subject_result.student_term_subject_result import calculate_year_results
			calculate_year_results(academic_year, student_group, submit_results)
		
		else:
			frappe.throw("Invalid calculation type")
			
		frappe.db.commit()
		
		if submit_results:
			return {"status": "success", "message": "Calculation completed and results submitted successfully"}
		else:
			return {"status": "success", "message": "Calculation completed and results saved as drafts"}
		
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Result calculation failed: {str(e)}")
		return {"status": "error", "message": str(e)}

# Student Application API endpoints

@frappe.whitelist(allow_guest=True)
def get_programs_for_application():
	"""Get all available programs for student application"""
	programs = [
		{"name": "Grade 1", "program_name": "Grade 1", "program_abbreviation": "GR1"},
		{"name": "Grade 2", "program_name": "Grade 2", "program_abbreviation": "GR2"},
		{"name": "Grade 3", "program_name": "Grade 3", "program_abbreviation": "GR3"},
		{"name": "Grade 4", "program_name": "Grade 4", "program_abbreviation": "GR4"},
		{"name": "Grade 5", "program_name": "Grade 5", "program_abbreviation": "GR5"},
		{"name": "Grade 6", "program_name": "Grade 6", "program_abbreviation": "GR6"},
		{"name": "Grade 7", "program_name": "Grade 7", "program_abbreviation": "GR7"},
		{"name": "Grade 8", "program_name": "Grade 8", "program_abbreviation": "GR8"},
		{"name": "Grade 1 AO", "program_name": "Grade 1 AO", "program_abbreviation": "GR1 AO"},
		{"name": "Grade 2 AO", "program_name": "Grade 2 AO", "program_abbreviation": "GR2 AO"},
		{"name": "Grade 3 AO", "program_name": "Grade 3 AO", "program_abbreviation": "GR3 AO"},
		{"name": "Grade 4 AO", "program_name": "Grade 4 AO", "program_abbreviation": "GR4 AO"},
		{"name": "Grade 5 AO", "program_name": "Grade 5 AO", "program_abbreviation": "GR5 AO"},
		{"name": "Grade 6 AO", "program_name": "Grade 6 AO", "program_abbreviation": "GR6 AO"},
		{"name": "Grade 7 AO", "program_name": "Grade 7 AO", "program_abbreviation": "GR7 AO"},
		{"name": "Grade 8 AO", "program_name": "Grade 8 AO", "program_abbreviation": "GR8 AO"},
		{"name": "Grade 9", "program_name": "Grade 9", "program_abbreviation": "GR9"},
		{"name": "Grade 10", "program_name": "Grade 10", "program_abbreviation": "GR10"},
		{"name": "Grade 11 NS", "program_name": "Grade 11 NS", "program_abbreviation": "GR11 NS"},
		{"name": "Grade 11 SS", "program_name": "Grade 11 SS", "program_abbreviation": "GR11 SS"},
		{"name": "Grade 12 NS", "program_name": "Grade 12 NS", "program_abbreviation": "GR12 NS"},
		{"name": "Grade 12 SS", "program_name": "Grade 12 SS", "program_abbreviation": "GR12 SS"},
		{"name": "LKG", "program_name": "LKG", "program_abbreviation": "LKG"},
		{"name": "UKG", "program_name": "UKG", "program_abbreviation": "UKG"},
		{"name": "LKG AO", "program_name": "LKG AO", "program_abbreviation": "LKG AO"},
		{"name": "UKG AO", "program_name": "UKG AO", "program_abbreviation": "UKG AO"},
		{"name": "Nursery", "program_name": "Nursery", "program_abbreviation": "NUR"},
		{"name": "Nursery AO", "program_name": "Nursery AO", "program_abbreviation": "NUR AO"},
	]
	return programs

@frappe.whitelist(allow_guest=True)
def get_education_levels():
	"""Get education level options"""
	return [
		"No Formal Education",
		"Primary School (1-8)",
		"Secondary School (9-10)",
		"Preparatory School (11-12)",
		"Certificate",
		"Diploma",
		"Bachelor's Degree",
		"Master's Degree",
		"PhD",
		"Other"
	]

@frappe.whitelist(allow_guest=True)
def get_occupation_options():
	"""Get occupation options"""
	return [
		"Government Employee",
		"Private Sector Employee",
		"Self-Employed/Business Owner",
		"Farmer",
		"Teacher",
		"Doctor",
		"Nurse",
		"Engineer",
		"Lawyer",
		"Accountant",
		"Driver",
		"Security Guard",
		"Shopkeeper",
		"Mechanic",
		"Electrician",
		"Carpenter",
		"Tailor",
		"Hairdresser",
		"Chef/Cook",
		"Cleaner",
		"Student",
		"Retired",
		"Unemployed",
		"Other"
	]

@frappe.whitelist(allow_guest=True)
def get_academic_years():
	"""Get all available academic years"""
	try:
		years = frappe.get_all(
			"Academic Year",
			fields=["name", "year_start_date", "year_end_date"],
			filters={"disabled": 0},
			order_by="year_start_date desc"
		)
		return years
	except Exception as e:
		frappe.log_error(message=str(e), title="Academic Years API Error")
		# Return a fallback list with the current academic year
		return [{"name": "2018 E.C.", "year_start_date": "2024-09-01", "year_end_date": "2025-08-31"}]

@frappe.whitelist(allow_guest=True)
def search_student_by_school_id(school_id):
	"""Search for existing student by school ID"""
	if not school_id:
		return None
	
	try:
		# First try to search in Student table
		student = frappe.get_all(
			"Student",
			fields=["name", "first_name", "middle_name", "last_name", "custom_school_id"],
			filters={"custom_school_id": school_id},
			limit=1
		)
		
		if student:
			return student[0]
		
		# If not found in Student table, try Student Applicant table
		applicant = frappe.get_all(
			"Student Applicant",
			fields=["name", "first_name", "middle_name", "last_name", "custom_school_id"],
			filters={"custom_school_id": school_id},
			limit=1
		)
		
		if applicant:
			return applicant[0]
			
		return None
		
	except Exception as e:
		# If there are permission issues, return None
		frappe.log_error(f"Error searching student by school ID: {str(e)}")
		return None

@frappe.whitelist(allow_guest=True)
def generate_school_id(branch="M1"):
	"""Generate a new school ID with format M1/*****/18 or M2/*****/18"""
	# Get the last used number for the branch
	last_id = frappe.db.sql("""
		SELECT custom_school_id 
		FROM `tabStudent Applicant` 
		WHERE custom_school_id LIKE %s 
		ORDER BY creation DESC 
		LIMIT 1
	""", (f"{branch}/%",), as_dict=True)
	
	if last_id:
		# Extract the number from the last ID
		parts = last_id[0]["custom_school_id"].split("/")
		if len(parts) == 3:
			try:
				last_num = int(parts[1])
				new_num = last_num + 1
			except ValueError:
				new_num = 10001
		else:
			new_num = 10001
	else:
		new_num = 10001
	
	# Format: M1/10001/18
	return f"{branch}/{new_num:05d}/18"

@frappe.whitelist(allow_guest=True)
def create_guardian(guardian_data):
	"""Create a new guardian record"""
	try:
		# Check required fields first
		if not guardian_data.get("guardian_name"):
			frappe.throw(_("Guardian name is required"))
		if not guardian_data.get("mobile_number"):
			frappe.throw(_("Mobile number is required"))
		
		# Format mobile number properly
		mobile_number = guardian_data.get("mobile_number", "").strip()
		if mobile_number and not mobile_number.startswith("+251"):
			mobile_number = f"+251{mobile_number}"
		
		# Check if guardian already exists by name and mobile number
		existing_guardian = frappe.get_all(
			"Guardian",
			filters={
				"guardian_name": guardian_data.get("guardian_name"),
				"mobile_number": mobile_number
			},
			limit=1
		)
		
		if existing_guardian:
			return existing_guardian[0].name
			
		guardian_doc = frappe.new_doc("Guardian")
		guardian_doc.guardian_name = guardian_data.get("guardian_name")
		guardian_doc.mobile_number = mobile_number
		
		# Optional fields
		if guardian_data.get("email_address"):
			guardian_doc.email_address = guardian_data.get("email_address")
		
		# Handle alternate number
		alternate_number = guardian_data.get("alternate_number", "").strip()
		if alternate_number and not alternate_number.startswith("+251"):
			alternate_number = f"+251{alternate_number}"
		if alternate_number:
			guardian_doc.alternate_number = alternate_number
		
		# Handle education field
		education = guardian_data.get("education")
		if education == "Other":
			education = guardian_data.get("education_other", education)
		if education:
			guardian_doc.education = education
		
		# Handle occupation field
		occupation = guardian_data.get("occupation")
		if occupation == "Other":
			occupation = guardian_data.get("occupation_other", occupation)
		if occupation:
			guardian_doc.occupation = occupation
		
		if guardian_data.get("work_address"):
			guardian_doc.work_address = guardian_data.get("work_address")
		
		# Handle image/photo field if present
		image_url = guardian_data.get("photo") or guardian_data.get("image")
		if image_url:
			guardian_doc.image = image_url
			
		guardian_doc.insert()
		return guardian_doc.name
	except Exception as e:
		error_msg = str(e)
		frappe.log_error(message=f"Guardian creation failed: {error_msg}\nData: {guardian_data}", title="Guardian Creation Error")
		frappe.throw(_("Error creating guardian: {0}").format(error_msg))

@frappe.whitelist(allow_guest=True)
def create_student_application(application_data):
	"""Create a new student application"""
	try:
		app_doc = frappe.new_doc("Student Applicant")
		
		# Check required fields
		if not application_data.get("first_name"):
			frappe.throw(_("First name is required"))
		if not application_data.get("last_name"):
			frappe.throw(_("Last name is required"))
		if not application_data.get("program"):
			frappe.throw(_("Program is required"))
		
		# Basic information
		app_doc.first_name = application_data.get("first_name")
		app_doc.middle_name = application_data.get("middle_name")
		app_doc.last_name = application_data.get("last_name")
		app_doc.custom_school_id = application_data.get("custom_school_id")
		app_doc.program = application_data.get("program")
		app_doc.academic_year = application_data.get("academic_year", "2018 E.C.")
		
		# Personal details
		app_doc.date_of_birth = application_data.get("date_of_birth")
		app_doc.gender = application_data.get("gender")
		app_doc.student_email_id = application_data.get("student_email_id")
		app_doc.student_mobile_number = application_data.get("primary_mobile_number") or application_data.get("student_mobile_number")
		app_doc.nationality = application_data.get("nationality", "Ethiopian")
		
		# Address - including new fields
		app_doc.address_line_1 = application_data.get("address_line_1")
		app_doc.address_line_2 = application_data.get("address_line_2")
		app_doc.kebele = application_data.get("kebele")
		app_doc.sub_city = application_data.get("sub_city")
		app_doc.city = application_data.get("city", "Adama")
		app_doc.state = application_data.get("state", "Oromia")
		app_doc.pincode = application_data.get("pincode")
		app_doc.country = application_data.get("country", "Ethiopia")
		
		# Application status
		app_doc.application_status = "Applied"
		
		# Image field
		if application_data.get("image"):
			app_doc.image = application_data.get("image")
		
		# Guardians
		guardians = application_data.get("guardians", [])
		for guardian in guardians:
			guardian_row = app_doc.append("guardians")
			guardian_row.guardian = guardian.get("guardian")
			guardian_row.guardian_name = guardian.get("guardian_name")
			guardian_row.relation = guardian.get("relation")
		
		# Siblings
		siblings = application_data.get("siblings", [])
		for sibling in siblings:
			sibling_row = app_doc.append("siblings")
			sibling_row.student = sibling.get("student")
			sibling_row.student_name = sibling.get("student_name")
			sibling_row.program = sibling.get("program")
			sibling_row.academic_year = sibling.get("academic_year")
		
		app_doc.insert()
		return app_doc.name
		
	except Exception as e:
		error_msg = str(e)
		frappe.log_error(message=f"Student application creation failed: {error_msg}\nData: {application_data}", title="Student Application Creation Error")
		frappe.throw(_("Error creating student application: {0}").format(error_msg))

@frappe.whitelist(allow_guest=True)
def get_application_by_id(application_id):
	"""Get student application details by ID"""
	try:
		app_doc = frappe.get_doc("Student Applicant", application_id)
		return app_doc.as_dict()
	except Exception as e:
		frappe.throw(_("Error fetching application: {0}").format(str(e)))

@frappe.whitelist(allow_guest=True)
def update_student_application(application_id, application_data):
	"""Update existing student application"""
	try:
		app_doc = frappe.get_doc("Student Applicant", application_id)
		
		# Update basic information
		app_doc.first_name = application_data.get("first_name")
		app_doc.middle_name = application_data.get("middle_name")
		app_doc.last_name = application_data.get("last_name")
		app_doc.custom_school_id = application_data.get("custom_school_id")
		app_doc.program = application_data.get("program")
		app_doc.academic_year = application_data.get("academic_year")
		
		# Update personal details
		app_doc.date_of_birth = application_data.get("date_of_birth")
		app_doc.gender = application_data.get("gender")
		app_doc.student_email_id = application_data.get("student_email_id")
		app_doc.student_mobile_number = application_data.get("primary_mobile_number") or application_data.get("student_mobile_number")
		app_doc.nationality = application_data.get("nationality", "Ethiopian")
		
		# Update address - including new fields
		app_doc.address_line_1 = application_data.get("address_line_1")
		app_doc.address_line_2 = application_data.get("address_line_2")
		app_doc.kebele = application_data.get("kebele")
		app_doc.sub_city = application_data.get("sub_city")
		app_doc.city = application_data.get("city", "Adama")
		app_doc.state = application_data.get("state", "Oromia")
		app_doc.pincode = application_data.get("pincode")
		app_doc.country = application_data.get("country", "Ethiopia")
		
		# Update guardians
		app_doc.guardians = []
		guardians = application_data.get("guardians", [])
		for guardian in guardians:
			guardian_row = app_doc.append("guardians")
			guardian_row.guardian = guardian.get("guardian")
			guardian_row.guardian_name = guardian.get("guardian_name")
			guardian_row.relation = guardian.get("relation")
		
		# Update siblings
		app_doc.siblings = []
		siblings = application_data.get("siblings", [])
		for sibling in siblings:
			sibling_row = app_doc.append("siblings")
			sibling_row.student = sibling.get("student")
			sibling_row.student_name = sibling.get("student_name")
			sibling_row.program = sibling.get("program")
			sibling_row.academic_year = sibling.get("academic_year")
		
		app_doc.save()
		return app_doc.name
		
	except Exception as e:
		frappe.log_error(message=str(e), title="Student Application Update Error")
		frappe.throw(_("Error updating student application: {0}").format(str(e)))

@frappe.whitelist(allow_guest=True)
def get_guardian_by_email(email):
	"""Get guardian by email address"""
	guardian = frappe.get_all(
		"Guardian",
		fields=["name", "guardian_name", "email_address", "mobile_number"],
		filters={"email_address": email},
		limit=1
	)
	
	if guardian:
		return guardian[0]
	return None

@frappe.whitelist(allow_guest=True)
def create_sibling_application(parent_application_id, sibling_data):
	"""Create a new sibling application using existing guardian information"""
	try:
		# Get parent application to copy guardian details
		parent_app = frappe.get_doc("Student Applicant", parent_application_id)
		
		# Create new application for sibling
		sibling_app = frappe.new_doc("Student Applicant")
		
		# Basic information
		sibling_app.first_name = sibling_data.get("first_name")
		sibling_app.middle_name = sibling_data.get("middle_name")
		sibling_app.last_name = sibling_data.get("last_name")
		sibling_app.custom_school_id = sibling_data.get("custom_school_id")
		sibling_app.program = sibling_data.get("program")
		sibling_app.academic_year = sibling_data.get("academic_year")
		
		# Personal details
		sibling_app.date_of_birth = sibling_data.get("date_of_birth")
		sibling_app.gender = sibling_data.get("gender")
		sibling_app.student_email_id = sibling_data.get("student_email_id")
		sibling_app.student_mobile_number = sibling_data.get("student_mobile_number")
		sibling_app.nationality = sibling_data.get("nationality", "Ethiopian")
		
		# Copy address from parent
		sibling_app.address_line_1 = parent_app.address_line_1
		sibling_app.address_line_2 = parent_app.address_line_2
		sibling_app.city = parent_app.city
		sibling_app.state = parent_app.state
		sibling_app.pincode = parent_app.pincode
		sibling_app.country = parent_app.country
		
		# Application status
		sibling_app.application_status = "Applied"
		
		# Copy guardians from parent
		for guardian in parent_app.guardians:
			guardian_row = sibling_app.append("guardians")
			guardian_row.guardian = guardian.guardian
			guardian_row.guardian_name = guardian.guardian_name
			guardian_row.relation = guardian.relation
		
		# Add sibling relationship
		sibling_row = sibling_app.append("siblings")
		sibling_row.student = parent_application_id
		sibling_row.student_name = f"{parent_app.first_name} {parent_app.middle_name or ''} {parent_app.last_name or ''}".strip()
		sibling_row.program = parent_app.program
		sibling_row.academic_year = parent_app.academic_year
		
		sibling_app.insert()
		
		# Update parent application to include this sibling
		parent_sibling_row = parent_app.append("siblings")
		parent_sibling_row.student = sibling_app.name
		parent_sibling_row.student_name = f"{sibling_app.first_name} {sibling_app.middle_name or ''} {sibling_app.last_name or ''}".strip()
		parent_sibling_row.program = sibling_app.program
		parent_sibling_row.academic_year = sibling_app.academic_year
		parent_app.save()
		
		return sibling_app.name
		
	except Exception as e:
		frappe.throw(_("Error creating sibling application: {0}").format(str(e)))

@frappe.whitelist(allow_guest=True)
def validate_phone_number(phone_number):
	"""Validate Ethiopian phone number format"""
	# Handle both direct parameter and JSON body
	if isinstance(phone_number, dict):
		phone_number = phone_number.get("phone_number", "")
	
	if not phone_number:
		return {"valid": False, "message": "Phone number is required"}
	
	# Remove any spaces or special characters
	phone_clean = ''.join(filter(str.isdigit, phone_number))
	
	# Check if it's exactly 9 digits
	if len(phone_clean) == 9:
		# Check if it starts with valid Ethiopian prefixes
		if phone_clean.startswith(('9', '7')):
			return {"valid": True, "message": "Valid phone number", "formatted": f"+251{phone_clean}"}
		else:
			return {"valid": False, "message": "Phone number must start with 9 or 7"}
	
	# Check if it's 10 digits starting with 0 (common mistake)
	elif len(phone_clean) == 10 and phone_clean.startswith('0'):
		return {"valid": False, "message": "Phone number should start with 9, not 0. Remove the leading 0."}
	
	# Check if it's too long or too short
	elif len(phone_clean) < 9:
		return {"valid": False, "message": "Phone number must be 9 digits long"}
	elif len(phone_clean) > 9:
		return {"valid": False, "message": "Phone number must be exactly 9 digits long"}
	
	else:
		return {"valid": False, "message": "Invalid phone number format"}

@frappe.whitelist(allow_guest=True)
def get_kebele_subcity_data():
	"""Get kebele and sub-city hierarchical data"""
	return {
		"Bole": [
			{"id": 1, "name": "Dhaka Adil"},
			{"id": 2, "name": "Gooro (01)"},
			{"id": 3, "name": "Dhadacha Araara (04)"}
		],
		"Gadaa": [
			{"id": 4, "name": "Badhatu (07)"},
			{"id": 5, "name": "Abba Gadaa (12)"},
			{"id": 6, "name": "Odaa (08)"},
			{"id": 7, "name": "Gurmuu (06)"}
		],
		"Bokkuu": [
			{"id": 8, "name": "Barreecha (11)"},
			{"id": 14, "name": "Migiiraa (02)"},
			{"id": 17, "name": "Bokku shanan"}
		],
		"Luugoo": [
			{"id": 9, "name": "Biqqa (10)"},
			{"id": 11, "name": "Gaara Luugo (03)"}
		],
		"Dambalaa": [
			{"id": 10, "name": "Dagaaga (05)"},
			{"id": 12, "name": "Irrechaa (09)"},
			{"id": 18, "name": "Malka"}
		],
		"Daabe": [
			{"id": 13, "name": "Caffee (13)"},
			{"id": 15, "name": "Daabe Solloqqe"},
			{"id": 16, "name": "Hangaatu (14)"}
		]
	}

@frappe.whitelist(allow_guest=True)
def generate_application_pdf(session_applications):
    """Generate PDF for one or more student applications"""
    try:
        from frappe.utils.pdf import get_pdf
        import json

        if isinstance(session_applications, str):
            session_applications = json.loads(session_applications)

        # School information
        logo_url = "https://app.makkobillischool.com/files/school_logo.png"
        school_name = "Makko Billi School"

        html_pages = []
        for app in session_applications:
            # Helper function to ensure absolute URLs for images
            def make_absolute_url(img_url):
                if not img_url:
                    return ''
                if img_url.startswith('http'):
                    return img_url
                site_url = frappe.utils.get_url()
                return site_url.rstrip('/') + '/' + img_url.lstrip('/')

            # Get and ensure proper image URLs
            student_img = make_absolute_url(app.get('studentData', {}).get('image', ''))
            father_img = make_absolute_url(app.get('fatherData', {}).get('image', ''))
            mother_img = make_absolute_url(app.get('motherData', {}).get('image', ''))
            guardian_img = make_absolute_url(app.get('guardianData', {}).get('image', ''))

            # Minimal PDF-safe styling with table-based layout
            html = f"""
            <html>
                <head>
                    <meta charset='utf-8'>
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif; 
                            margin: 10px; 
                            font-size: 10px; 
                            line-height: 1.2; 
                            color: #000;
                        }}
                        .header {{ 
                            text-align: center; 
                            margin-bottom: 15px; 
                            padding-bottom: 8px; 
                            border-bottom: 2px solid #333;
                        }}
                        .logo {{ 
                            width: 50px; 
                            height: 50px; 
                            margin-bottom: 5px;
                        }}
                        .school-name {{ 
                            font-size: 16px; 
                            font-weight: bold; 
                            margin: 3px 0;
                        }}
                        .app-title {{ 
                            font-size: 12px; 
                            margin: 3px 0;
                        }}
                        .app-id {{ 
                            font-size: 9px; 
                            color: #666;
                        }}
                        .main-container {{
                            display: table;
                            width: 100%;
                            margin-top: 10px;
                        }}
                        .left-column {{
                            display: table-cell;
                            width: 75%;
                            vertical-align: top;
                            padding-right: 10px;
                        }}
                        .right-column {{
                            display: table-cell;
                            width: 25%;
                            vertical-align: top;
                            text-align: center;
                        }}
                        .student-photo {{ 
                            width: 80px; 
                            height: 100px; 
                            border: 1px solid #333;
                            margin-bottom: 10px;
                        }}
                        .section {{ 
                            margin: 8px 0; 
                        }}
                        .section-title {{ 
                            font-size: 11px; 
                            font-weight: bold; 
                            margin-bottom: 4px; 
                            border-bottom: 1px solid #666;
                            padding-bottom: 2px;
                        }}
                        .info-table {{ 
                            width: 100%; 
                            border-collapse: collapse; 
                            margin: 3px 0; 
                        }}
                        .info-table td {{ 
                            padding: 2px 4px; 
                            vertical-align: top; 
                            border-bottom: 1px solid #eee;
                        }}
                        .label {{ 
                            font-weight: bold; 
                            width: 35%; 
                        }}
                        .guardian-photos {{ 
                            text-align: center; 
                            margin: 5px 0; 
                        }}
                        .parent-photo {{ 
                            width: 60px; 
                            height: 70px; 
                            border: 1px solid #333; 
                            margin: 0 2px; 
                            display: inline-block;
                        }}
                    </style>
                </head>
                <body>
                    <!-- Header with logo and school info -->
                    <div class='header'>
                        <img src='{logo_url}' alt='School Logo' class='logo'>
                        <div class='school-name'>{school_name}</div>
                        <div class='app-title'>Student Application Form</div>
                        <div class='app-id'>Application ID: {app.get('submittedApplicationId', 'N/A')}</div>
                    </div>

                    <div class='main-container'>
                        <div class='left-column'>
                            <!-- Student Information -->
                            <div class='section'>
                                <div class='section-title'>Student Information</div>
                                <table class='info-table'>
                                    <tr>
                                        <td class='label'>Full Name:</td>
                                        <td>{app.get('studentData', {}).get('first_name', '')} {app.get('studentData', {}).get('middle_name', '')} {app.get('studentData', {}).get('last_name', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Date of Birth:</td>
                                        <td>{app.get('studentData', {}).get('date_of_birth', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Gender:</td>
                                        <td>{app.get('studentData', {}).get('gender', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Program/Grade:</td>
                                        <td>{app.get('studentData', {}).get('program', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Email:</td>
                                        <td>{app.get('studentData', {}).get('student_email_id', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>School ID:</td>
                                        <td>{app.get('studentData', {}).get('custom_school_id', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Mobile:</td>
                                        <td>{app.get('studentData', {}).get('primary_mobile_number', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Student Type:</td>
                                        <td>{app.get('studentType', '').title()}</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Address Information -->
                            <div class='section'>
                                <div class='section-title'>Address Information</div>
                                <table class='info-table'>
                                    <tr>
                                        <td class='label'>Home Address:</td>
                                        <td>{app.get('studentData', {}).get('address_line_1', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Sub-city:</td>
                                        <td>{app.get('studentData', {}).get('sub_city', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Kebele:</td>
                                        <td>{app.get('studentData', {}).get('kebele', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>City:</td>
                                        <td>{app.get('studentData', {}).get('city', 'Adama')}</td>
                                    </tr>
                                </table>
                            </div>
            """

            # Guardian Information based on type
            if app.get("guardianType") == "parent":
                html += f"""
                            <!-- Guardian Information (Parents) -->
                            <div class='section'>
                                <div class='section-title'>Guardian Information</div>
                                <table class='info-table'>
                                    <tr>
                                        <td class='label'>Father's Name:</td>
                                        <td>{app.get('fatherData', {}).get('guardian_name', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Father's Mobile:</td>
                                        <td>{app.get('fatherData', {}).get('mobile_number', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Father's Email:</td>
                                        <td>{app.get('fatherData', {}).get('email_address', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Father's Occupation:</td>
                                        <td>{app.get('fatherData', {}).get('occupation', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Mother's Name:</td>
                                        <td>{app.get('motherData', {}).get('guardian_name', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Mother's Mobile:</td>
                                        <td>{app.get('motherData', {}).get('mobile_number', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Mother's Email:</td>
                                        <td>{app.get('motherData', {}).get('email_address', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Mother's Occupation:</td>
                                        <td>{app.get('motherData', {}).get('occupation', '')}</td>
                                    </tr>
                                </table>
                                <div class='guardian-photos'>
                                    {f"<img src='{father_img}' class='parent-photo' alt='Father Photo'>" if father_img else ""}
                                    {f"<img src='{mother_img}' class='parent-photo' alt='Mother Photo'>" if mother_img else ""}
                                </div>
                            </div>
                """
            else:
                html += f"""
                            <!-- Guardian Information (Single Guardian) -->
                            <div class='section'>
                                <div class='section-title'>Guardian Information</div>
                                <table class='info-table'>
                                    <tr>
                                        <td class='label'>Guardian Name:</td>
                                        <td>{app.get('guardianData', {}).get('guardian_name', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Mobile:</td>
                                        <td>{app.get('guardianData', {}).get('mobile_number', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Email:</td>
                                        <td>{app.get('guardianData', {}).get('email_address', '')}</td>
                                    </tr>
                                    <tr>
                                        <td class='label'>Occupation:</td>
                                        <td>{app.get('guardianData', {}).get('occupation', '')}</td>
                                    </tr>
                                </table>
                                <div class='guardian-photos'>
                                    {f"<img src='{guardian_img}' class='parent-photo' alt='Guardian Photo'>" if guardian_img else ""}
                                </div>
                            </div>
                """

            html += f"""
                        </div>
                        <div class='right-column'>
                            <!-- Student Photo -->
                            {f"<img src='{student_img}' class='student-photo' alt='Student Photo'>" if student_img else "<div class='student-photo'></div>"}
                        </div>
                    </div>
                </body>
            </html>
            """
            html_pages.append(html)

        # Join pages with page breaks for multiple applications
        full_html = ("<div style='page-break-before: always;'></div>").join(html_pages)
        
        # Enhanced PDF options for better rendering
        pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'encoding': "UTF-8",
            'load-error-handling': 'ignore',
            'load-media-error-handling': 'ignore',
            'disable-javascript': None,
            'quiet': None
        }

        pdf_content = get_pdf(full_html, options=pdf_options)
        
        if not pdf_content:
            frappe.throw(_("Failed to generate PDF content"))
        
        # Use application ID for filename
        app_id = session_applications[0].get('submittedApplicationId', 'unknown') if session_applications else 'unknown'
        frappe.local.response.filename = f"student_application_{app_id}.pdf"
        frappe.local.response.filecontent = pdf_content
        frappe.local.response.type = "download"
        return pdf_content
    except Exception as e:
        frappe.log_error(message=str(e), title="PDF Generation Error")
        frappe.throw(_("Error generating PDF: {0}").format(str(e)))

@frappe.whitelist(allow_guest=True)
def check_duplicate_application():
	"""Check if an application already exists with the given email or mobile number"""
	try:
		email = frappe.form_dict.get('email')
		mobile = frappe.form_dict.get('mobile')
		
		if not email and not mobile:
			return {"exists": False}
		
		filters = []
		if email:
			filters.append(['Student Applicant', 'student_email_id', '=', email])
		if mobile:
			filters.append(['Student Applicant', 'guardian_mobile_number', '=', mobile])
		
		# Check if any student applicant exists with the given criteria
		existing = frappe.get_all('Student Applicant', 
			filters=filters, 
			limit=1,
			or_filters=True
		)
		
		return {"exists": len(existing) > 0}
		
	except Exception as e:
		frappe.log_error(f"Error checking duplicate application: {str(e)}")
		return {"exists": False, "error": str(e)}

@frappe.whitelist(allow_guest=True)
def upload_file_guest():
	"""Upload file for guest users (student application images) - Enhanced version"""
	try:
		import frappe
		from frappe.utils.file_manager import save_file
		from frappe.core.doctype.file.file import create_new_folder
		import os
		import base64
		
		# Temporarily set session user to Administrator for file operations
		frappe.set_user("Administrator")
		
		if 'file' not in frappe.request.files:
			frappe.throw(_("No file was uploaded"))
		
		file = frappe.request.files['file']
		if file.filename == '':
			frappe.throw(_("No file selected"))
		
		# Read file content
		file_content = file.read()
		
		# Check file size (limit to 5MB)
		if len(file_content) > 5 * 1024 * 1024:
			frappe.throw(_("File size should not exceed 5MB"))
		
		# Check file type
		allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
		file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
		if file_ext not in allowed_extensions:
			frappe.throw(_("Only image files (PNG, JPG, JPEG, GIF, WEBP) are allowed"))
		
		# Create a unique filename
		import uuid
		unique_name = str(uuid.uuid4())[:8]
		new_filename = f"student_app_{unique_name}_{file.filename}"
		
		# Ensure the folder exists
		folder_name = "Home/Student Applications"
		try:
			# Try to create folder if it doesn't exist
			if not frappe.db.exists("File", {"is_folder": 1, "file_name": "Student Applications", "folder": "Home"}):
				create_new_folder("Student Applications", "Home")
		except:
			# If folder creation fails, use Home folder
			folder_name = "Home"
		
		# Save file using Frappe's save_file with Administrator privileges
		try:
			# Create File document directly
			file_doc = frappe.new_doc("File")
			file_doc.file_name = new_filename
			file_doc.is_private = 0  # Make it public
			file_doc.folder = folder_name
			
			# Save file content to disk
			import tempfile
			with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
				temp_file.write(file_content)
				temp_file_path = temp_file.name
			
			# Read the file and save it properly
			with open(temp_file_path, 'rb') as f:
				file_doc.content = f.read()
			
			# Clean up temp file
			os.unlink(temp_file_path)
			
			# Insert the document
			file_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			
			# Ensure the file URL is accessible
			file_url = file_doc.file_url
			if not file_url.startswith('http'):
				# Make sure we have a full URL for PDF generation
				site_url = frappe.utils.get_url()
				file_url = site_url + file_url
			
			return {
				"file_name": file_doc.file_name,
				"file_url": file_url,
				"name": file_doc.name
			}
			
		except Exception as e:
			frappe.log_error(message=str(e), title="File Upload Error - Primary Method")
			
			# Fallback method using save_file with Administrator privileges
			try:
				file_doc = save_file(
					new_filename,
					file_content,
					"",  # dt (doctype) - empty for standalone file
					"",  # dn (document name) - empty for standalone file
					folder=folder_name,
					decode=False,
					is_private=0  # Make it public so it can be accessed in PDFs
				)
				
				# Ensure the file URL is accessible
				file_url = file_doc.file_url
				if not file_url.startswith('http'):
					# Make sure we have a full URL for PDF generation
					site_url = frappe.utils.get_url()
					file_url = site_url + file_url
				
				return {
					"file_name": file_doc.file_name,
					"file_url": file_url,
					"name": file_doc.name
				}
				
			except Exception as e2:
				frappe.log_error(message=str(e2), title="File Upload Error - Fallback Method")
				
				# Final fallback - create file record manually
				try:
					# Encode file content as base64 for storage
					file_content_b64 = base64.b64encode(file_content).decode('utf-8')
					
					# Create file record in database directly
					file_doc_name = frappe.generate_hash(length=10)
					file_record = {
						'doctype': 'File',
						'name': file_doc_name,
						'file_name': new_filename,
						'is_private': 0,
						'folder': folder_name,
						'file_size': len(file_content),
						'content_hash': frappe.generate_hash(file_content),
						'file_url': f'/files/{new_filename}'
					}
					
					frappe.get_doc(file_record).insert(ignore_permissions=True)
					frappe.db.commit()
					
					# Save actual file to disk
					from frappe.utils import get_site_path
					files_path = get_site_path('public', 'files')
					if not os.path.exists(files_path):
						os.makedirs(files_path)
					
					file_path = os.path.join(files_path, new_filename)
					with open(file_path, 'wb') as f:
						f.write(file_content)
					
					file_url = f'/files/{new_filename}'
					if not file_url.startswith('http'):
						site_url = frappe.utils.get_url()
						file_url = site_url + file_url
					
					return {
						"file_name": new_filename,
						"file_url": file_url,
						"name": file_doc_name
					}
					
				except Exception as e3:
					frappe.log_error(message=str(e3), title="File Upload Error - Final Fallback")
					frappe.throw(_("Error saving file: {0}").format(str(e3)))
			
	except Exception as e:
		frappe.log_error(message=str(e), title="File Upload Error - Main")
		frappe.throw(_("Error uploading file: {0}").format(str(e)))
	
	finally:
		# Reset user session
		frappe.set_user("Guest")

@frappe.whitelist(allow_guest=True)
def has_file_permission(doc, user=None, permission_type="read"):
	"""Custom permission handler for File doctype to allow guest uploads for student applications"""
	try:
		# Allow guest users to upload files for student applications
		if user == "Guest" and permission_type in ["create", "write"]:
			# Check if this is a student application related file
			if doc and hasattr(doc, 'file_name') and 'student_app_' in str(doc.file_name):
				return True
			# Also allow for files in Student Applications folder
			if doc and hasattr(doc, 'folder') and 'Student Applications' in str(doc.folder):
				return True
		
		# For all other cases, use default permission logic
		return None  # This will fall back to standard permission checking
	except:
		return None
