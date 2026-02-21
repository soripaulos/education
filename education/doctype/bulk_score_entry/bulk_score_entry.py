# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

ASSESSMENT_MAX_SCORES = {
	"First Test": 15,
	"Second Test": 15,
	"Mid Exam": 20,
	"Final Exam": 50,
}


class BulkScoreEntry(Document):
	def on_submit(self):
		max_score = ASSESSMENT_MAX_SCORES.get(self.assessment_criteria)
		if max_score is None:
			frappe.throw(_("Max score not defined for Assessment Criteria: {0}").format(self.assessment_criteria))

		success_count = 0
		failed_students = []

		for student_entry in self.students:
			if student_entry.score is not None:
				try:
					if student_entry.score > max_score:
						raise ValueError(_("Score ({0}) cannot be greater than {1}").format(student_entry.score, max_score))
					if student_entry.score < 0:
						raise ValueError(_("Score cannot be negative"))

					self.create_student_assessment_score(student_entry, max_score)
					success_count += 1
				
				except Exception as e:
					failed_students.append(student_entry.student_name)
					frappe.log_error(
						message=f"Failed to create Assessment Score for Student: {student_entry.student} ({student_entry.student_name})",
						title="Bulk Score Entry Submission Error"
					)

		if failed_students:
			message = _("Successfully created {0} records. ").format(success_count)
			message += _("Failed to create records for: {0}. ").format(", ".join(failed_students))
			message += _("Please check the Error Log for more details.")
			frappe.msgprint(message, title=_("Partial Success"), indicator="orange")
		else:
			frappe.msgprint(_("Successfully created and submitted records for all {0} students.").format(success_count), title=_("Success"), indicator="green")


	def create_student_assessment_score(self, student_entry, max_score):
		doc = frappe.new_doc("Student Assessment Score")
		doc.academic_year = self.academic_year
		doc.academic_term = self.academic_term
		doc.student_group = self.student_group
		doc.course = self.course
		doc.assessment_criteria = self.assessment_criteria
		doc.max_score = max_score
		doc.student = student_entry.student
		doc.score = student_entry.score
		doc.save(ignore_permissions=True)
		doc.submit()

@frappe.whitelist()
def get_max_score(assessment_criteria):
	return ASSESSMENT_MAX_SCORES.get(assessment_criteria)


@frappe.whitelist()
def get_students(student_group):
	if not student_group:
		frappe.throw(_("Please select a Student Group first"))

	student_list = frappe.get_all(
		"Student Group Student",
		filters={"parent": student_group},
		fields=["student", "student_name"],
		order_by="student_name",
		as_list=1,
	)

	return student_list

@frappe.whitelist()
def process_scores_from_mobile(scores_data):
	"""
	Receives a list of student scores from a mobile app and creates Student Assessment Score documents.
	:param scores_data: JSON string representing a dictionary with keys:
						'academic_year', 'academic_term', 'student_group', 'course', 'assessment_criteria',
						and 'scores' (a list of {'student': 'student_id', 'score': score_value})
	"""
	import json
	data = json.loads(scores_data)

	required_fields = ['academic_year', 'academic_term', 'student_group', 'course', 'assessment_criteria', 'scores']
	for field in required_fields:
		if field not in data:
			frappe.throw(_("Missing required field in payload: {0}").format(field))

	max_score = ASSESSMENT_MAX_SCORES.get(data['assessment_criteria'])
	if max_score is None:
		frappe.throw(_("Max score not defined for Assessment Criteria: {0}").format(data['assessment_criteria']))

	success_count = 0
	failed_entries = []

	for entry in data['scores']:
		student_id = entry.get('student')
		score = entry.get('score')
		student_name = frappe.db.get_value("Student", student_id, "student_name")

		try:
			if score is None:
				continue

			if score > max_score:
				raise ValueError(_("Score ({0}) cannot be greater than {1}").format(score, max_score))
			if score < 0:
				raise ValueError(_("Score cannot be negative"))

			doc = frappe.new_doc("Student Assessment Score")
			doc.academic_year = data['academic_year']
			doc.academic_term = data['academic_term']
			doc.student_group = data['student_group']
			doc.course = data['course']
			doc.assessment_criteria = data['assessment_criteria']
			doc.max_score = max_score
			doc.student = student_id
			doc.score = score
			doc.save(ignore_permissions=True)
			doc.submit()
			success_count += 1

		except Exception as e:
			failed_entries.append({'student': student_name, 'error': str(e)})
			frappe.log_error(
				message=f"Failed to create Assessment Score for Student: {student_id} ({student_name}). Error: {e}",
				title="Mobile Score Entry Error"
			)

	if failed_entries:
		return {
			"status": "Partial Success",
			"success_count": success_count,
			"message": f"Successfully created {success_count} records. {len(failed_entries)} records failed.",
			"failures": failed_entries
		}
	
	return {
		"status": "Success",
		"message": f"Successfully created and submitted records for all {success_count} students."
	} 