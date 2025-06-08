# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from education.education.utils import validate_duplicate_student


class StudentGroup(Document):
	def validate(self):
		self.validate_mandatory_fields()
		self.validate_strength()
		self.validate_students()
		self.validate_and_set_child_table_fields()
		validate_duplicate_student(self.students)

	def validate_mandatory_fields(self):
		if self.group_based_on == "Course" and not self.course:
			frappe.throw(_("Please select Course"))
		if self.group_based_on == "Course" and (not self.program and self.batch):
			frappe.throw(_("Please select Program"))
		if self.group_based_on == "Batch" and not self.program:
			frappe.throw(_("Please select Program"))

	def validate_strength(self):
		if cint(self.max_strength) < 0:
			frappe.throw(_("""Max strength cannot be less than zero."""))
		if self.max_strength and len(self.students) > self.max_strength:
			frappe.throw(
				_("""Cannot enroll more than {0} students for this student group.""").format(
					self.max_strength
				)
			)

	def validate_students(self):
		program_enrollment = get_program_enrollment(
			self.academic_year,
			self.academic_term,
			self.program,
			self.batch,
			self.student_category,
			self.course,
		)
		students = [d.student for d in program_enrollment] if program_enrollment else []
		for d in self.students:
			if (
				not frappe.db.get_value("Student", d.student, "enabled")
				and d.active
				and not self.disabled
			):
				frappe.throw(
					_("{0} - {1} is inactive student").format(d.group_roll_number, d.student_name)
				)

			if (
				(self.group_based_on == "Batch")
				and cint(frappe.defaults.get_defaults().validate_batch)
				and d.student not in students
			):
				frappe.throw(
					_("{0} - {1} is not enrolled in the Batch {2}").format(
						d.group_roll_number, d.student_name, self.batch
					)
				)

			if (
				(self.group_based_on == "Course")
				and cint(frappe.defaults.get_defaults().validate_course)
				and (d.student not in students)
			):
				frappe.throw(
					_("{0} - {1} is not enrolled in the Course {2}").format(
						d.group_roll_number, d.student_name, self.course
					)
				)

	def validate_and_set_child_table_fields(self):
		roll_numbers = [d.group_roll_number for d in self.students if d.group_roll_number]
		max_roll_no = max(roll_numbers) if roll_numbers else 0
		roll_no_list = []
		for d in self.students:
			if not d.student_name:
				d.student_name = frappe.db.get_value("Student", d.student, "title")
			if not d.group_roll_number:
				max_roll_no += 1
				d.group_roll_number = max_roll_no
			if d.group_roll_number in roll_no_list:
				frappe.throw(_("Duplicate roll number for student {0}").format(d.student_name))
			else:
				roll_no_list.append(d.group_roll_number)


@frappe.whitelist()
def get_students(
	academic_year,
	group_based_on,
	academic_term=None,
	program=None,
	batch=None,
	student_category=None,
	course=None,
):
	enrolled_students = get_program_enrollment(
		academic_year, academic_term, program, batch, student_category, course
	)

	if enrolled_students:
		student_list = []
		for s in enrolled_students:
			if frappe.db.get_value("Student", s.student, "enabled"):
				s.update({"active": 1})
			else:
				s.update({"active": 0})
			student_list.append(s)
		return student_list
	else:
		frappe.msgprint(_("No students found"))
		return []


def get_program_enrollment(
	academic_year,
	academic_term=None,
	program=None,
	batch=None,
	student_category=None,
	course=None,
):

	condition1 = " "
	condition2 = " "
	if academic_term:
		condition1 += " and pe.academic_term = %(academic_term)s"
	if program:
		condition1 += " and pe.program = %(program)s"
	if batch:
		condition1 += " and pe.student_batch_name = %(batch)s"
	if student_category:
		condition1 += " and pe.student_category = %(student_category)s"
	if course:
		condition1 += " and pe.name = pec.parent and pec.course = %(course)s"
		condition2 = ", `tabProgram Enrollment Course` pec"

	return frappe.db.sql(
		"""
		select
			pe.student, pe.student_name
		from
			`tabProgram Enrollment` pe {condition2}
		where
			pe.academic_year = %(academic_year)s
			and pe.docstatus = 1 {condition1}
		order by
			pe.student_name asc
		""".format(
			condition1=condition1, condition2=condition2
		),
		(
			{
				"academic_year": academic_year,
				"academic_term": academic_term,
				"program": program,
				"batch": batch,
				"student_category": student_category,
				"course": course,
			}
		),
		as_dict=1,
	)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def fetch_students(doctype, txt, searchfield, start, page_len, filters):
	if filters.get("group_based_on") != "Activity":
		enrolled_students = get_program_enrollment(
			filters.get("academic_year"),
			filters.get("academic_term"),
			filters.get("program"),
			filters.get("batch"),
			filters.get("student_category"),
		)
		student_group_student = frappe.db.sql_list(
			"""select student from `tabStudent Group Student` where parent=%s""",
			(filters.get("student_group")),
		)
		students = (
			[d.student for d in enrolled_students if d.student not in student_group_student]
			if enrolled_students
			else [""]
		) or [""]
		return frappe.db.sql(
			"""select name, student_name from tabStudent
			where name in ({0}) and (`{1}` LIKE %s or student_name LIKE %s)
			order by idx desc, name
			limit %s, %s""".format(
				", ".join(["%s"] * len(students)), searchfield
			),
			tuple(students + ["%%%s%%" % txt, "%%%s%%" % txt, start, page_len]),
		)
	else:
		return frappe.db.sql(
			"""select name, student_name from tabStudent
			where `{0}` LIKE %s or student_name LIKE %s
			order by idx desc, name
			limit %s, %s""".format(
				searchfield
			),
			tuple(["%%%s%%" % txt, "%%%s%%" % txt, start, page_len]),
		)

# ---- Result Entry Functions ----

def _create_and_submit_single_result(roster_plan, student, score):
	"""Helper function to create and submit a single student result. Not whitelisted."""
	try:
		roster_plan_doc = frappe.get_doc("Roster Plan", roster_plan)
		student_doc = frappe.get_doc("Student", student)

		if not roster_plan_doc:
			raise ValueError(f"Roster Plan {roster_plan} not found.")
		if not student_doc:
			raise ValueError(f"Student {student} not found.")

		score_value = float(score)
		max_score = float(roster_plan_doc.maximum_assessment_score)

		if score_value < 0:
			raise ValueError("Score cannot be negative.")
		if score_value > max_score:
			raise ValueError(f"Score ({score_value}) cannot be greater than max score ({max_score}).")

		if frappe.db.exists("Student Term Subject Result", {"roster_plan": roster_plan, "student": student, "docstatus": 1}):
			raise ValueError("Submitted result for this student and roster plan already exists.")

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
	except Exception as e:
		# Re-raise the exception to be caught by the bulk function
		raise e

@frappe.whitelist()
def create_and_submit_bulk_term_subject_results(results_json):
	"""
	Whitelist method to accept a list of student results and process them.
	`results_json` is expected to be a JSON string array of objects,
	each object containing 'roster_plan', 'student', and 'score'.
	"""
	try:
		results = frappe.parse_json(results_json)
	except Exception:
		frappe.throw(_("Invalid JSON data provided."), title="JSON Error")

	if not isinstance(results, list):
		frappe.throw(_("Payload must be a list of student results."))

	success_count = 0
	failures = []

	for result in results:
		try:
			_create_and_submit_single_result(
				roster_plan=result.get('roster_plan'),
				student=result.get('student'),
				score=result.get('score')
			)
			success_count += 1
		except Exception as e:
			student_name = frappe.db.get_value("Student", result.get('student'), "student_name", cache=True) or result.get('student')
			failures.append({"student": student_name, "error": str(e)})
			frappe.log_error(f"Failed to submit for student {student_name}: {e}", "Bulk Submission Individual Failure")
	
	return {
		"success_count": success_count,
		"failure_count": len(failures),
		"failures": failures
	}
