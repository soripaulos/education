# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from collections import defaultdict

class RankCalculation(Document):
	pass

@frappe.whitelist()
def calculate_ranks(doc_name):
	doc = frappe.get_doc("Rank Calculation", doc_name)
	if doc.calculation_type == "Term End":
		return calculate_term_ranks(doc)
	elif doc.calculation_type == "Year End":
		return calculate_year_ranks(doc)

def calculate_term_ranks(doc):
	if not doc.academic_term:
		frappe.throw(_("Please select an Academic Term for Term End calculation."))

	# Clear existing draft reports
	existing_reports = frappe.get_all("Student Term Report", filters={"academic_term": doc.academic_term, "student_group": doc.student_group, "docstatus": 0})
	for report in existing_reports:
		frappe.delete_doc("Student Term Report", report.name, ignore_permissions=True)

	scores = frappe.get_all(
		"Student Assessment Score",
		filters={"academic_term": doc.academic_term, "student_group": doc.student_group, "docstatus": 1},
		fields=["student", "course", "score"]
	)

	if not scores:
		return {"message": "No submitted scores found for the selected criteria.", "html": "<h3>No Scores Found</h3>"}

	# {student: {course: total_score}}
	student_course_scores = defaultdict(lambda: defaultdict(float))
	for r in scores:
		student_course_scores[r.student][r.course] += r.score
	
	# {student: average_score}
	student_averages = {}
	for student, courses in student_course_scores.items():
		total_score = sum(courses.values())
		average = total_score / len(courses) if courses else 0
		student_averages[student] = average

		# Create report
		report = frappe.new_doc("Student Term Report")
		report.academic_year = doc.academic_year
		report.academic_term = doc.academic_term
		report.student_group = doc.student_group
		report.student = student
		report.term_average = average
		for course, total in courses.items():
			report.append("course_summary", {"course": course, "total_score_for_term": total})
		report.save(ignore_permissions=True)

	# Calculate Ranks
	sorted_students = sorted(student_averages.items(), key=lambda x: x[1], reverse=True)
	
	ranks = {}
	last_score = -1
	last_rank = 0
	for i, (student, score) in enumerate(sorted_students):
		current_rank = i + 1
		if score == last_score:
			ranks[student] = last_rank
		else:
			ranks[student] = current_rank
			last_rank = current_rank
		last_score = score

	# Update reports with ranks
	for student, rank in ranks.items():
		report_name = frappe.db.get_value("Student Term Report", {"student": student, "academic_term": doc.academic_term, "student_group": doc.student_group, "docstatus": 0})
		if report_name:
			frappe.db.set_value("Student Term Report", report_name, "rank_in_group", rank)

	html = "<h3>Term Ranks Calculated Successfully</h3><p>Draft Student Term Reports have been created. You can review and submit them.</p>"
	return {"message": "Success", "html": html}


def calculate_year_ranks(doc):
	# Clear existing draft reports
	existing_reports = frappe.get_all("Student Year Report", filters={"academic_year": doc.academic_year, "student_group": doc.student_group, "docstatus": 0})
	for report in existing_reports:
		frappe.delete_doc("Student Year Report", report.name, ignore_permissions=True)

	term_reports = frappe.get_all(
		"Student Term Report",
		filters={"academic_year": doc.academic_year, "student_group": doc.student_group, "docstatus": 1},
		fields=["student", "term_average"]
	)

	if not term_reports:
		return {"message": "No submitted term reports found for the selected criteria.", "html": "<h3>No Term Reports Found</h3>"}

	# {student: [list of term averages]}
	student_term_averages = defaultdict(list)
	for r in term_reports:
		student_term_averages[r.student].append(r.term_average)

	# {student: year_average}
	student_year_averages = {}
	for student, averages in student_term_averages.items():
		year_average = sum(averages) / len(averages) if averages else 0
		student_year_averages[student] = year_average
		
		report = frappe.new_doc("Student Year Report")
		report.academic_year = doc.academic_year
		report.student_group = doc.student_group
		report.student = student
		report.year_average = year_average
		
		# Trigger validation which will call calculate_year_summary_for_courses
		report.validate()
		
		report.save(ignore_permissions=True)

	# Calculate Ranks
	sorted_students = sorted(student_year_averages.items(), key=lambda x: x[1], reverse=True)
	
	ranks = {}
	last_score = -1
	last_rank = 0
	for i, (student, score) in enumerate(sorted_students):
		current_rank = i + 1
		if score == last_score:
			ranks[student] = last_rank
		else:
			ranks[student] = current_rank
			last_rank = current_rank
		last_score = score

	# Update reports with ranks
	for student, rank in ranks.items():
		report_name = frappe.db.get_value("Student Year Report", {"student": student, "academic_year": doc.academic_year, "student_group": doc.student_group, "docstatus": 0})
		if report_name:
			frappe.db.set_value("Student Year Report", report_name, "rank_in_group", rank)
	
	html = "<h3>Year Ranks Calculated Successfully</h3><p>Draft Student Year Reports have been created. You can review and submit them.</p>"
	return {"message": "Success", "html": html} 