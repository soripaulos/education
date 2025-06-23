# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today, random_string

# Disable QR code functionality for Frappe Cloud compatibility
QR_CODE_AVAILABLE = False


class StudentReportCard(Document):
	def autoname(self):
		"""Generate a random Report ID and set it as the document name."""
		if not self.report_id:
			self.report_id = self.generate_report_id()
		self.name = self.report_id

	def validate(self):
		"""Populate all data before saving."""
		self.populate_student_details()
		self.fetch_academic_data()
		self.generate_html_content()
		self.generate_qr_code()
		
		if self.is_new():
			self.is_published = 1

	def generate_report_id(self):
		"""Generate a random 5-character alphanumeric ID."""
		while True:
			report_id = random_string(5).upper()
			if not frappe.db.exists("Student Report Card", {"report_id": report_id}):
				return report_id

	def populate_student_details(self):
		"""Populate student details from Student master"""
		if self.student:
			try:
				student_doc = frappe.get_doc("Student", self.student)
				self.student_name = student_doc.student_name
				self.student_id_number = student_doc.student_email_id or self.student
				self.student_gender = student_doc.gender or "Not Specified"
				
				# Calculate age from date of birth
				if student_doc.date_of_birth:
					birth_date = getdate(student_doc.date_of_birth)
					today_date = getdate(today())
					age = today_date.year - birth_date.year
					if today_date.month < birth_date.month or (today_date.month == birth_date.month and today_date.day < birth_date.day):
						age -= 1
					self.student_age = age
				
				# Get class name and program from student group
				if self.student_group:
					group_doc = frappe.get_doc("Student Group", self.student_group)
					self.class_name = group_doc.group_name
					self.program = group_doc.program
			except:
				pass

	def fetch_academic_data(self):
		"""Fetch academic data from Student Term Report and Student Year Report"""
		if not self.student or not self.academic_year or not self.student_group:
			return
		
		try:
			# Get academic terms for the year
			terms = frappe.get_all("Academic Term", 
				filters={"academic_year": self.academic_year},
				fields=["name", "term_name"],
				order_by="term_start_date"
			)
			
			# Fetch Term 1 data
			if len(terms) >= 1:
				term_1_report = frappe.get_value("Student Term Report", {
					"student": self.student,
					"academic_year": self.academic_year,
					"academic_term": terms[0].name,
					"student_group": self.student_group,
					"docstatus": 1
				}, ["term_average", "rank_in_group"], as_dict=True)
				
				if term_1_report:
					self.term_1_average = flt(term_1_report.term_average, 3)
					self.term_1_rank = term_1_report.rank_in_group
			
			# Fetch Term 2 data
			if len(terms) >= 2:
				term_2_report = frappe.get_value("Student Term Report", {
					"student": self.student,
					"academic_year": self.academic_year,
					"academic_term": terms[1].name,
					"student_group": self.student_group,
					"docstatus": 1
				}, ["term_average", "rank_in_group"], as_dict=True)
				
				if term_2_report:
					self.term_2_average = flt(term_2_report.term_average, 3)
					self.term_2_rank = term_2_report.rank_in_group
			
			# Fetch Year data
			year_report = frappe.get_value("Student Year Report", {
				"student": self.student,
				"academic_year": self.academic_year,
				"student_group": self.student_group,
				"docstatus": 1
			}, ["year_average", "rank_in_group"], as_dict=True)
			
			if year_report:
				self.year_average = flt(year_report.year_average, 3)
				self.year_rank = year_report.rank_in_group
		except:
			pass

	def generate_html_content(self):
		"""Generate HTML content for the report card"""
		
		# Get school/company information
		try:
			default_company = frappe.db.get_single_value("Global Defaults", "default_company")
			company_doc = frappe.get_doc("Company", default_company) if default_company else None
		except:
			company_doc = None
		
		# Simple verification section without QR code
		verification_section = f"""
		<div class="qr-section">
			<div class="section-title">Verification</div>
			<div class="verification-text">
				<strong>Report ID: {self.report_id}</strong><br>
				Verify this report at: <a href="{self.qr_code_url or '#'}" target="_blank">app.makkobillischool.com</a><br>
				<span class="verification-bold">Only reports from app.makkobillischool.com are authentic.</span>
			</div>
		</div>
		"""
		
		html_content = f"""
		<!DOCTYPE html>
		<html lang="en">
		<head>
			<meta charset="UTF-8">
			<meta name="viewport" content="width=device-width, initial-scale=1.0">
			<title>Student Report Card - {self.student_name}</title>
			<style>
				* {{
					margin: 0;
					padding: 0;
					box-sizing: border-box;
				}}
				
				body {{
					font-family: 'Arial', sans-serif;
					line-height: 1.6;
					color: #333;
					background-color: #f8f9fa;
				}}
				
				.container {{
					max-width: 800px;
					margin: 20px auto;
					background: white;
					border-radius: 10px;
					box-shadow: 0 0 20px rgba(0,0,0,0.1);
					overflow: hidden;
				}}
				
				.header {{
					background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
					color: white;
					padding: 30px;
					text-align: center;
					position: relative;
				}}
				
				.logo {{
					width: 80px;
					height: 80px;
					margin: 0 auto 15px;
					background: white;
					border-radius: 50%;
					display: flex;
					align-items: center;
					justify-content: center;
				}}
				
				.logo img {{
					max-width: 60px;
					max-height: 60px;
				}}
				
				.school-name {{
					font-size: 24px;
					font-weight: bold;
					margin-bottom: 5px;
				}}
				
				.report-title {{
					font-size: 18px;
					opacity: 0.9;
				}}
				
				.student-info {{
					padding: 30px;
					background: #f8f9fa;
					border-bottom: 2px solid #e9ecef;
				}}
				
				.info-grid {{
					display: grid;
					grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
					gap: 20px;
				}}
				
				.info-item {{
					background: white;
					padding: 15px;
					border-radius: 8px;
					border-left: 4px solid #667eea;
				}}
				
				.info-label {{
					font-size: 12px;
					color: #6c757d;
					text-transform: uppercase;
					letter-spacing: 0.5px;
					margin-bottom: 5px;
				}}
				
				.info-value {{
					font-size: 16px;
					font-weight: 600;
					color: #2c3e50;
				}}
				
				.performance-summary {{
					padding: 30px;
				}}
				
				.section-title {{
					font-size: 20px;
					font-weight: bold;
					color: #2c3e50;
					margin-bottom: 20px;
					text-align: center;
					position: relative;
				}}
				
				.section-title::after {{
					content: '';
					position: absolute;
					bottom: -5px;
					left: 50%;
					transform: translateX(-50%);
					width: 50px;
					height: 3px;
					background: #667eea;
				}}
				
				.performance-grid {{
					display: grid;
					grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
					gap: 20px;
					margin-bottom: 30px;
				}}
				
				.performance-card {{
					background: white;
					padding: 20px;
					border-radius: 10px;
					text-align: center;
					border: 2px solid #e9ecef;
					transition: transform 0.3s ease;
				}}
				
				.performance-card:hover {{
					transform: translateY(-5px);
					box-shadow: 0 5px 15px rgba(0,0,0,0.1);
				}}
				
				.performance-label {{
					font-size: 12px;
					color: #6c757d;
					text-transform: uppercase;
					margin-bottom: 10px;
				}}
				
				.performance-value {{
					font-size: 24px;
					font-weight: bold;
					color: #2c3e50;
				}}
				
				.qr-section {{
					padding: 30px;
					text-align: center;
					background: white;
					border-top: 2px solid #e9ecef;
				}}
				
				.verification-text {{
					font-size: 14px;
					color: #6c757d;
					margin-top: 15px;
				}}
				
				.verification-bold {{
					font-weight: bold;
					color: #dc3545;
				}}
				
				@media (max-width: 768px) {{
					.container {{
						margin: 10px;
						border-radius: 0;
					}}
					
					.info-grid {{
						grid-template-columns: 1fr;
					}}
					
					.performance-grid {{
						grid-template-columns: repeat(2, 1fr);
					}}
				}}
			</style>
		</head>
		<body>
			<div class="container">
				<div class="header">
					<div class="logo">
						<img src="/files/school_logo.png" alt="School Logo" onerror="this.style.display='none'">
					</div>
					<div class="school-name">{company_doc.company_name if company_doc else 'Makko Bills School'}</div>
					<div class="report-title">Student Report Card</div>
				</div>
				
				<div class="student-info">
					<div class="info-grid">
						<div class="info-item">
							<div class="info-label">Student Name</div>
							<div class="info-value">{self.student_name or ''}</div>
						</div>
						<div class="info-item">
							<div class="info-label">Gender</div>
							<div class="info-value">{self.student_gender or 'Not Specified'}</div>
						</div>
						<div class="info-item">
							<div class="info-label">Age</div>
							<div class="info-value">{self.student_age or 'N/A'}</div>
						</div>
						<div class="info-item">
							<div class="info-label">Class</div>
							<div class="info-value">{self.class_name or ''}</div>
						</div>
						<div class="info-item">
							<div class="info-label">Academic Year</div>
							<div class="info-value">{self.academic_year or ''}</div>
						</div>
						<div class="info-item">
							<div class="info-label">Report ID</div>
							<div class="info-value">{self.report_id or ''}</div>
						</div>
					</div>
				</div>
				
				<div class="performance-summary">
					<div class="section-title">Performance Summary</div>
					<div class="performance-grid">
		"""
		
		# Add performance cards
		if self.term_1_average:
			html_content += f"""
						<div class="performance-card">
							<div class="performance-label">Term 1 Average</div>
							<div class="performance-value">{self.term_1_average:.1f}</div>
						</div>
						<div class="performance-card">
							<div class="performance-label">Term 1 Rank</div>
							<div class="performance-value">{self.term_1_rank or 'N/A'}</div>
						</div>
			"""
		
		if self.term_2_average:
			html_content += f"""
						<div class="performance-card">
							<div class="performance-label">Term 2 Average</div>
							<div class="performance-value">{self.term_2_average:.1f}</div>
						</div>
						<div class="performance-card">
							<div class="performance-label">Term 2 Rank</div>
							<div class="performance-value">{self.term_2_rank or 'N/A'}</div>
						</div>
			"""
		
		if self.year_average:
			html_content += f"""
						<div class="performance-card">
							<div class="performance-label">Year Average</div>
							<div class="performance-value">{self.year_average:.1f}</div>
						</div>
						<div class="performance-card">
							<div class="performance-label">Year Rank</div>
							<div class="performance-value">{self.year_rank or 'N/A'}</div>
						</div>
			"""
		
		html_content += """
					</div>
				</div>
		"""
		
		# Add verification section
		html_content += verification_section
		html_content += """
			</div>
		</body>
		</html>
		"""
		
		self.html_content = html_content

	def generate_qr_code(self):
		"""Generate QR code URL for the report card"""
		base_url = "https://app.makkobillischool.com"
		self.qr_code_url = f"{base_url}/report-card/{self.report_id}"


@frappe.whitelist()
def bulk_generate_report_cards(academic_year, student_group, regenerate=False):
	"""Generate report cards for all students in a group"""
	
	if not academic_year or not student_group:
		frappe.throw("Academic Year and Student Group are required")
	
	# Get all students in the group
	students = frappe.get_all("Student Group Student", 
		filters={"parent": student_group, "active": 1},
		fields=["student", "student_name"]
	)
	
	if not students:
		frappe.throw("No active students found in the selected group")
	
	generated_count = 0
	skipped_count = 0
	
	for student in students:
		try:
			# Check if report card already exists
			existing_report = frappe.db.exists("Student Report Card", {
				"student": student.student,
				"academic_year": academic_year,
				"student_group": student_group
			})
			
			if existing_report and not regenerate:
				skipped_count += 1
				continue
			
			# Delete existing report if regenerating
			if existing_report and regenerate:
				frappe.delete_doc("Student Report Card", existing_report)
			
			# Create new report card
			report_card = frappe.new_doc("Student Report Card")
			report_card.student = student.student
			report_card.academic_year = academic_year
			report_card.student_group = student_group
			report_card.insert()
			generated_count += 1
		except Exception as e:
			frappe.log_error(f"Error generating report card for {student.student}: {str(e)}")
			continue
	
	message = f"Generated {generated_count} report cards"
	if skipped_count > 0:
		message += f", skipped {skipped_count} existing reports"
	
	frappe.msgprint(message)
	
	return {
		"generated": generated_count,
		"skipped": skipped_count,
		"total": len(students)
	}


@frappe.whitelist()
def get_report_card_html(report_id):
	"""Get HTML content for public viewing"""
	try:
		report_card = frappe.get_doc("Student Report Card", {"report_id": report_id})
		
		if not report_card or not report_card.is_published:
			frappe.throw("Report card not found or not published")
		
		return report_card.html_content
	except:
		frappe.throw("Report card not found") 