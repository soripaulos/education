# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, today
import json


@frappe.whitelist(allow_guest=True)
def get_student_report_cards(student=None, academic_year=None, limit=20):
	"""Get list of report cards for a student"""
	
	filters = {}
	if student:
		filters["student"] = student
	if academic_year:
		filters["academic_year"] = academic_year
	
	# Only show published report cards for guest users
	if frappe.session.user == "Guest":
		filters["is_published"] = 1
		filters["docstatus"] = 1
	
	report_cards = frappe.get_all("Student Report Card",
		filters=filters,
		fields=[
			"name", "report_id", "student", "student_name", 
			"academic_year", "student_group", "class_name",
			"term_1_average", "term_2_average", "year_average",
			"term_1_rank", "term_2_rank", "year_rank",
			"is_published", "creation", "modified"
		],
		order_by="creation desc",
		limit=limit
	)
	
	return {
		"status": "success",
		"data": report_cards,
		"count": len(report_cards)
	}


@frappe.whitelist(allow_guest=True)
def get_report_card_by_id(report_id):
	"""Get a specific report card by its ID"""
	
	if not report_id:
		frappe.throw(_("Report ID is required"))
	
	try:
		report_card = frappe.get_doc("Student Report Card", {"report_id": report_id})
		
		# Check if report card is published for guest users
		if frappe.session.user == "Guest":
			if not report_card.is_published or report_card.docstatus != 1:
				frappe.throw(_("Report card not found or not published"))
		
		# Prepare response data
		data = {
			"report_id": report_card.report_id,
			"student": report_card.student,
			"student_name": report_card.student_name,
			"student_id_number": report_card.student_id_number,
			"student_age": report_card.student_age,
			"student_gender": report_card.student_gender,
			"academic_year": report_card.academic_year,
			"student_group": report_card.student_group,
			"class_name": report_card.class_name,
			"program": report_card.program,
			"term_1_average": report_card.term_1_average,
			"term_1_rank": report_card.term_1_rank,
			"term_2_average": report_card.term_2_average,
			"term_2_rank": report_card.term_2_rank,
			"year_average": report_card.year_average,
			"year_rank": report_card.year_rank,
			"qr_code_url": report_card.qr_code_url,
			"html_content": report_card.html_content,
			"is_published": report_card.is_published,
			"creation": report_card.creation,
			"modified": report_card.modified
		}
		
		# Add subject data
		data["term_1_subjects"] = []
		for subject in report_card.term_1_subjects:
			data["term_1_subjects"].append({
				"course": subject.course,
				"course_name": frappe.db.get_value("Course", subject.course, "course_name"),
				"total_score_for_term": subject.total_score_for_term,
				"total_maximum_score": subject.total_maximum_score,
				"percentage": subject.percentage
			})
		
		data["term_2_subjects"] = []
		for subject in report_card.term_2_subjects:
			data["term_2_subjects"].append({
				"course": subject.course,
				"course_name": frappe.db.get_value("Course", subject.course, "course_name"),
				"total_score_for_term": subject.total_score_for_term,
				"total_maximum_score": subject.total_maximum_score,
				"percentage": subject.percentage
			})
		
		data["year_subjects"] = []
		for subject in report_card.year_subjects:
			data["year_subjects"].append({
				"course": subject.course,
				"course_name": frappe.db.get_value("Course", subject.course, "course_name"),
				"total_year_score": subject.total_year_score,
				"total_year_max_score": subject.total_year_max_score,
				"year_average_percentage": subject.year_average_percentage,
				"terms_count": subject.terms_count
			})
		
		return {
			"status": "success",
			"data": data
		}
		
	except frappe.DoesNotExistError:
		frappe.throw(_("Report card not found"))
	except Exception as e:
		frappe.log_error(f"Error fetching report card {report_id}: {str(e)}")
		frappe.throw(_("Error fetching report card"))


@frappe.whitelist()
def generate_report_card_pdf(report_id):
	"""Generate PDF for a report card"""
	
	if not report_id:
		frappe.throw(_("Report ID is required"))
	
	try:
		report_card = frappe.get_doc("Student Report Card", {"report_id": report_id})
		
		# Generate PDF using Frappe's PDF generation
		from frappe.utils.pdf import get_pdf
		
		html = report_card.html_content
		pdf = get_pdf(html, {
			"page-size": "A4",
			"margin-top": "0.5in",
			"margin-right": "0.5in",
			"margin-bottom": "0.5in",
			"margin-left": "0.5in",
			"encoding": "UTF-8",
			"no-outline": None
		})
		
		# Save PDF as file
		from frappe.utils.file_manager import save_file
		
		file_name = f"Report_Card_{report_card.student_name}_{report_card.academic_year}.pdf"
		file_doc = save_file(file_name, pdf, "Student Report Card", report_card.name, is_private=0)
		
		# Update report card with PDF file
		report_card.pdf_file = file_doc.file_url
		report_card.save()
		
		return {
			"status": "success",
			"message": "PDF generated successfully",
			"file_url": file_doc.file_url
		}
		
	except Exception as e:
		frappe.log_error(f"Error generating PDF for report card {report_id}: {str(e)}")
		frappe.throw(_("Error generating PDF"))


@frappe.whitelist()
def get_student_list(student_group=None, academic_year=None):
	"""Get list of students for report card generation"""
	
	filters = {}
	if student_group:
		# Get students from student group
		students = frappe.get_all("Student Group Student",
			filters={"parent": student_group, "active": 1},
			fields=["student", "student_name"]
		)
		return {
			"status": "success",
			"data": students,
			"count": len(students)
		}
	else:
		# Get all active students
		students = frappe.get_all("Student",
			filters={"enabled": 1},
			fields=["name", "student_name", "student_email_id", "gender"],
			order_by="student_name",
			limit=100
		)
		return {
			"status": "success",
			"data": students,
			"count": len(students)
		}


@frappe.whitelist()
def get_academic_years():
	"""Get list of academic years"""
	
	academic_years = frappe.get_all("Academic Year",
		fields=["name", "year_name", "year_start_date", "year_end_date"],
		order_by="year_start_date desc"
	)
	
	return {
		"status": "success",
		"data": academic_years,
		"count": len(academic_years)
	}


@frappe.whitelist()
def get_student_groups(academic_year=None):
	"""Get list of student groups"""
	
	filters = {}
	if academic_year:
		filters["academic_year"] = academic_year
	
	student_groups = frappe.get_all("Student Group",
		filters=filters,
		fields=["name", "group_name", "academic_year", "program", "academic_term"],
		order_by="group_name"
	)
	
	return {
		"status": "success",
		"data": student_groups,
		"count": len(student_groups)
	}


@frappe.whitelist()
def get_academic_terms(academic_year=None):
	"""Get list of academic terms"""
	
	filters = {}
	if academic_year:
		filters["academic_year"] = academic_year
	
	academic_terms = frappe.get_all("Academic Term",
		filters=filters,
		fields=["name", "term_name", "academic_year", "term_start_date", "term_end_date"],
		order_by="term_start_date"
	)
	
	return {
		"status": "success",
		"data": academic_terms,
		"count": len(academic_terms)
	}


@frappe.whitelist()
def bulk_generate_report_cards_api(academic_year, student_group, regenerate=False):
	"""API endpoint for bulk generation of report cards"""
	
	try:
		from education.education.doctype.student_report_card.student_report_card import bulk_generate_report_cards
		
		result = bulk_generate_report_cards(academic_year, student_group, regenerate)
		
		return {
			"status": "success",
			"message": "Bulk generation completed",
			"data": result
		}
		
	except Exception as e:
		frappe.log_error(f"Error in bulk generation: {str(e)}")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist(allow_guest=True)
def get_school_info():
	"""Get school/company information for branding"""
	
	try:
		default_company = frappe.db.get_single_value("Global Defaults", "default_company")
		
		if default_company:
			company = frappe.get_doc("Company", default_company)
			return {
				"status": "success",
				"data": {
					"company_name": company.company_name,
					"company_logo": company.company_logo,
					"country": company.country,
					"default_currency": company.default_currency
				}
			}
		else:
			return {
				"status": "success",
				"data": {
					"company_name": "Makko Bills School",
					"company_logo": "/files/school_logo.png",
					"country": "Kenya",
					"default_currency": "KES"
				}
			}
			
	except Exception as e:
		frappe.log_error(f"Error fetching school info: {str(e)}")
		return {
			"status": "error",
			"message": "Error fetching school information"
		} 