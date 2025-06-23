# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_context(context):
	"""Get context for report card web page"""
	
	# Get report ID from URL path
	path_parts = frappe.request.path.strip('/').split('/')
	report_id = None
	
	# Extract report ID from URL like /report-card/ABC123
	if len(path_parts) >= 2 and path_parts[0] == 'report-card':
		report_id = path_parts[1]
	
	if not report_id:
		frappe.throw(_("Report ID is required"), frappe.DoesNotExistError)
	
	try:
		# Get the report card document
		report_card = frappe.get_doc("Student Report Card", {"report_id": report_id})
		
		# Check if report card is published
		if not report_card.is_published or report_card.docstatus != 1:
			frappe.throw(_("Report card not found or not published"), frappe.DoesNotExistError)
		
		# Set context variables
		context.report_card = report_card
		context.html_content = report_card.html_content
		context.student_name = report_card.student_name
		context.report_id = report_card.report_id
		context.title = f"Report Card - {report_card.student_name}"
		
		# Add meta tags for SEO
		context.metatags = {
			"title": f"Report Card - {report_card.student_name}",
			"description": f"Academic Report Card for {report_card.student_name} - {report_card.academic_year}",
			"keywords": "report card, student report, academic performance, grades"
		}
		
	except frappe.DoesNotExistError:
		frappe.throw(_("Report card not found"), frappe.DoesNotExistError)
	except Exception as e:
		frappe.log_error(f"Error loading report card {report_id}: {str(e)}")
		frappe.throw(_("Error loading report card"), frappe.ValidationError) 