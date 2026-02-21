#!/usr/bin/env python3
"""
Setup script for Student Term Results Summary Report
Run this script to install and configure the report

Usage:
    bench --site [site-name] execute education.setup_student_report.setup
    
Or from bench console:
    bench --site [site-name] console
    >>> from education.setup_student_report import setup
    >>> setup()
"""

import frappe
from frappe import _


def setup():
	"""
	Main setup function to install the report
	"""
	print("=" * 60)
	print("Student Term Results Summary Report - Setup")
	print("=" * 60)
	
	try:
		# Step 1: Check if report exists
		print("\n[1/5] Checking if report exists...")
		if frappe.db.exists("Report", "Student Term Results Summary"):
			print("✓ Report already exists")
			report = frappe.get_doc("Report", "Student Term Results Summary")
		else:
			print("✗ Report not found in database")
			print("    Please ensure report files are in:")
			print("    education/education/report/student_term_results_summary/")
			return False
		
		# Step 2: Set permissions
		print("\n[2/5] Setting up permissions...")
		setup_permissions(report)
		print("✓ Permissions configured")
		
		# Step 3: Clear cache
		print("\n[3/5] Clearing cache...")
		frappe.clear_cache()
		print("✓ Cache cleared")
		
		# Step 4: Verify DocType
		print("\n[4/5] Verifying Student Term Subject Result DocType...")
		if frappe.db.exists("DocType", "Student Term Subject Result"):
			print("✓ Student Term Subject Result DocType exists")
		else:
			print("✗ Student Term Subject Result DocType not found")
			print("    Please create this DocType first")
			return False
		
		# Step 5: Test query
		print("\n[5/5] Testing report query...")
		test_report()
		
		print("\n" + "=" * 60)
		print("✓ Setup completed successfully!")
		print("=" * 60)
		print("\nYou can now access the report at:")
		print("Home > Education > Reports > Student Term Results Summary")
		print("\nOr directly at:")
		print(f"{frappe.utils.get_url()}/app/query-report/Student%20Term%20Results%20Summary")
		print("\n")
		
		return True
		
	except Exception as e:
		print(f"\n✗ Setup failed: {str(e)}")
		frappe.log_error(frappe.get_traceback(), "Student Report Setup Error")
		return False


def setup_permissions(report):
	"""
	Configure role permissions for the report
	"""
	required_roles = [
		"Education Manager",
		"Instructor",
		"Academics User",
		"System Manager"
	]
	
	# Get existing roles
	existing_roles = [r.role for r in report.roles]
	
	# Add missing roles
	added_roles = []
	for role in required_roles:
		if role not in existing_roles:
			report.append("roles", {"role": role})
			added_roles.append(role)
	
	if added_roles:
		report.save()
		frappe.db.commit()
		print(f"    Added roles: {', '.join(added_roles)}")
	else:
		print("    All roles already configured")


def test_report():
	"""
	Test if the report can be loaded and executed
	"""
	try:
		# Try to import the report module
		from education.education.report.student_term_results_summary import student_term_results_summary
		
		# Test with empty filters (should return empty or throw descriptive error)
		try:
			columns, data, msg, chart = student_term_results_summary.execute({})
			print("✓ Report module loaded successfully")
		except Exception as e:
			if "Please select" in str(e):
				print("✓ Report module loaded successfully")
			else:
				raise e
		
	except ImportError as e:
		print(f"✗ Failed to import report module: {str(e)}")
		raise
	except Exception as e:
		print(f"⚠ Warning: {str(e)}")


def create_sample_data():
	"""
	Create sample data for testing the report
	Only run this in development/test environments!
	"""
	print("\n" + "=" * 60)
	print("Creating Sample Data")
	print("=" * 60)
	print("\n⚠ WARNING: This will create test data in your system")
	print("Only proceed if you're in a development/test environment\n")
	
	confirm = input("Type 'YES' to continue: ")
	if confirm != "YES":
		print("Cancelled")
		return
	
	try:
		# Check prerequisites
		if not frappe.db.exists("Academic Year", "2024-25"):
			print("Creating Academic Year: 2024-25")
			ay = frappe.get_doc({
				"doctype": "Academic Year",
				"academic_year_name": "2024-25",
				"year_start_date": "2024-04-01",
				"year_end_date": "2025-03-31"
			})
			ay.insert()
		
		# Create semester
		if not frappe.db.exists("Academic Term", "Term 1 2024-25"):
			print("Creating Academic Term: Term 1 2024-25")
			term = frappe.get_doc({
				"doctype": "Academic Term",
				"academic_year": "2024-25",
				"term_name": "Term 1 2024-25",
				"term_start_date": "2024-04-01",
				"term_end_date": "2024-09-30"
			})
			term.insert()
		
		# Create program
		if not frappe.db.exists("Program", "Grade 10"):
			print("Creating Program: Grade 10")
			program = frappe.get_doc({
				"doctype": "Program",
				"program_name": "Grade 10",
				"program_code": "GRD10"
			})
			program.insert()
		
		# Create courses
		subjects = ["Mathematics", "English", "Science", "History", "Geography"]
		for subject in subjects:
			if not frappe.db.exists("Course", subject):
				print(f"Creating Course: {subject}")
				course = frappe.get_doc({
					"doctype": "Course",
					"course_name": subject,
					"course_code": subject[:3].upper()
				})
				course.insert()
		
		# Create assessment criteria
		exams = ["Midterm Exam", "Final Exam", "Quiz 1"]
		for exam in exams:
			if not frappe.db.exists("Assessment Criteria", exam):
				print(f"Creating Assessment Criteria: {exam}")
				criteria = frappe.get_doc({
					"doctype": "Assessment Criteria",
					"assessment_criteria": exam,
					"assessment_criteria_group": "All Assessment Groups"
				})
				criteria.insert()
		
		# Create student group
		if not frappe.db.exists("Student Group", "Grade 10 A - Test"):
			print("Creating Student Group: Grade 10 A - Test")
			sg = frappe.get_doc({
				"doctype": "Student Group",
				"student_group_name": "Grade 10 A - Test",
				"academic_year": "2024-25",
				"group_based_on": "Batch",
				"program": "Grade 10"
			})
			sg.insert()
		
		# Create sample students and results
		student_names = ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Prince", "Ethan Hunt"]
		
		for i, name in enumerate(student_names):
			student_id = f"STU-TEST-{i+1:03d}"
			
			# Create student if not exists
			if not frappe.db.exists("Student", student_id):
				print(f"Creating Student: {name}")
				student = frappe.get_doc({
					"doctype": "Student",
					"student_name": name,
					"first_name": name.split()[0],
					"last_name": name.split()[1] if len(name.split()) > 1 else "",
				})
				student.insert()
				
				# Add to student group
				sg = frappe.get_doc("Student Group", "Grade 10 A - Test")
				sg.append("students", {
					"student": student.name,
					"student_name": name
				})
				sg.save()
			
			# Create results for each subject and exam
			import random
			for subject in subjects:
				for exam in exams[:2]:  # Only midterm and final
					# Random score between 60-100
					score = random.randint(60, 100)
					max_score = 100
					
					# Check if result already exists
					existing = frappe.db.exists("Student Term Subject Result", {
						"student": student_id,
						"subject": subject,
						"exam": exam,
						"semester": "Term 1 2024-25",
						"academic_year": "2024-25"
					})
					
					if not existing:
						print(f"  Creating result: {name} - {subject} - {exam}: {score}/{max_score}")
						result = frappe.get_doc({
							"doctype": "Student Term Subject Result",
							"naming_series": "STSR-.YYYY.-",
							"student": student_id,
							"student_name": name,
							"academic_year": "2024-25",
							"semester": "Term 1 2024-25",
							"subject": subject,
							"student_group": "Grade 10 A - Test",
							"grade": "Grade 10",
							"exam": exam,
							"score": score,
							"max_score": max_score
						})
						result.insert()
						result.submit()
		
		frappe.db.commit()
		
		print("\n✓ Sample data created successfully!")
		print("\nYou can now test the report with:")
		print("  Student Group: Grade 10 A - Test")
		print("  Academic Year: 2024-25")
		print("  Semester: Term 1 2024-25")
		
	except Exception as e:
		print(f"\n✗ Failed to create sample data: {str(e)}")
		frappe.log_error(frappe.get_traceback(), "Sample Data Creation Error")
		frappe.db.rollback()


def verify_installation():
	"""
	Verify that the report is properly installed and working
	"""
	print("\n" + "=" * 60)
	print("Verifying Installation")
	print("=" * 60)
	
	checks = []
	
	# Check 1: Report exists
	print("\n[1/6] Checking if report exists in database...")
	if frappe.db.exists("Report", "Student Term Results Summary"):
		print("✓ Report exists")
		checks.append(True)
	else:
		print("✗ Report not found")
		checks.append(False)
	
	# Check 2: Report files exist
	print("\n[2/6] Checking report files...")
	import os
	report_path = frappe.get_app_path("education", "education", "report", "student_term_results_summary")
	required_files = [
		"__init__.py",
		"student_term_results_summary.json",
		"student_term_results_summary.js",
		"student_term_results_summary.py"
	]
	
	all_files_exist = True
	for file in required_files:
		file_path = os.path.join(report_path, file)
		if os.path.exists(file_path):
			print(f"  ✓ {file}")
		else:
			print(f"  ✗ {file} missing")
			all_files_exist = False
	
	checks.append(all_files_exist)
	
	# Check 3: DocType exists
	print("\n[3/6] Checking Student Term Subject Result DocType...")
	if frappe.db.exists("DocType", "Student Term Subject Result"):
		print("✓ DocType exists")
		checks.append(True)
	else:
		print("✗ DocType not found")
		checks.append(False)
	
	# Check 4: Permissions
	print("\n[4/6] Checking permissions...")
	report = frappe.get_doc("Report", "Student Term Results Summary")
	roles = [r.role for r in report.roles]
	if "Education Manager" in roles or "System Manager" in roles:
		print(f"✓ Permissions configured: {', '.join(roles)}")
		checks.append(True)
	else:
		print("⚠ No roles assigned")
		checks.append(False)
	
	# Check 5: Module import
	print("\n[5/6] Testing module import...")
	try:
		from education.education.report.student_term_results_summary import student_term_results_summary
		print("✓ Module imports successfully")
		checks.append(True)
	except ImportError as e:
		print(f"✗ Import failed: {str(e)}")
		checks.append(False)
	
	# Check 6: Sample data
	print("\n[6/6] Checking for sample data...")
	count = frappe.db.count("Student Term Subject Result", {"docstatus": 1})
	if count > 0:
		print(f"✓ Found {count} submitted result(s)")
		checks.append(True)
	else:
		print("⚠ No submitted results found (report will be empty)")
		print("  Run create_sample_data() to generate test data")
		checks.append(False)
	
	# Summary
	print("\n" + "=" * 60)
	passed = sum(checks)
	total = len(checks)
	print(f"Verification: {passed}/{total} checks passed")
	
	if passed == total:
		print("✓ Installation verified successfully!")
	elif passed >= 4:
		print("⚠ Installation mostly complete with minor issues")
	else:
		print("✗ Installation has issues that need to be resolved")
	
	print("=" * 60)
	
	return passed == total


# CLI interface
if __name__ == "__main__":
	import sys
	
	if len(sys.argv) > 1:
		command = sys.argv[1]
		
		if command == "setup":
			setup()
		elif command == "verify":
			verify_installation()
		elif command == "sample-data":
			create_sample_data()
		else:
			print("Unknown command. Available commands:")
			print("  setup        - Install and configure the report")
			print("  verify       - Verify installation")
			print("  sample-data  - Create sample test data")
	else:
		print("Usage: bench --site [site] execute education.setup_student_report.[command]")
		print("\nCommands:")
		print("  setup        - Install and configure the report")
		print("  verify       - Verify installation")
		print("  sample-data  - Create sample test data")
