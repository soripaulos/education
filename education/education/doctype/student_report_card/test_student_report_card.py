# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import today, getdate


class TestStudentReportCard(unittest.TestCase):
	def setUp(self):
		"""Set up test data"""
		self.create_test_data()
	
	def create_test_data(self):
		"""Create test data for report card testing"""
		
		# Create test academic year if it doesn't exist
		if not frappe.db.exists("Academic Year", "2024-25"):
			academic_year = frappe.new_doc("Academic Year")
			academic_year.academic_year_name = "2024-25"
			academic_year.year_start_date = "2024-04-01"
			academic_year.year_end_date = "2025-03-31"
			academic_year.insert()
		
		# Create test student if it doesn't exist
		if not frappe.db.exists("Student", "TEST-STU-001"):
			student = frappe.new_doc("Student")
			student.first_name = "Test"
			student.last_name = "Student"
			student.student_email_id = "test.student@school.com"
			student.gender = "Male"
			student.date_of_birth = "2010-01-01"
			student.insert()
		
		# Create test program if it doesn't exist
		if not frappe.db.exists("Program", "Test Program"):
			program = frappe.new_doc("Program")
			program.program_name = "Test Program"
			program.insert()
		
		# Create test student group if it doesn't exist
		if not frappe.db.exists("Student Group", "Test Class 2024"):
			student_group = frappe.new_doc("Student Group")
			student_group.group_name = "Test Class 2024"
			student_group.academic_year = "2024-25"
			student_group.program = "Test Program"
			student_group.insert()
	
	def test_report_card_creation(self):
		"""Test basic report card creation"""
		
		report_card = frappe.new_doc("Student Report Card")
		report_card.student = "TEST-STU-001"
		report_card.academic_year = "2024-25"
		report_card.student_group = "Test Class 2024"
		report_card.report_type = "Full Report"
		
		# Insert the document
		report_card.insert()
		
		# Check if report ID was generated
		self.assertIsNotNone(report_card.report_id)
		self.assertTrue(len(report_card.report_id) == 5)
		
		# Check if student details were populated
		self.assertEqual(report_card.student_name, "Test Student")
		self.assertEqual(report_card.student_gender, "Male")
		
		# Check if QR code URL was generated
		self.assertIsNotNone(report_card.qr_code_url)
		self.assertIn("app.makkobillischool.com", report_card.qr_code_url)
		
		# Check if HTML content was generated
		self.assertIsNotNone(report_card.html_content)
		self.assertIn("Test Student", report_card.html_content)
	
	def test_report_id_uniqueness(self):
		"""Test that report IDs are unique"""
		
		# Create first report card
		report_card1 = frappe.new_doc("Student Report Card")
		report_card1.student = "TEST-STU-001"
		report_card1.academic_year = "2024-25"
		report_card1.student_group = "Test Class 2024"
		report_card1.insert()
		
		# Create second report card
		report_card2 = frappe.new_doc("Student Report Card")
		report_card2.student = "TEST-STU-001"
		report_card2.academic_year = "2024-25"
		report_card2.student_group = "Test Class 2024"
		report_card2.insert()
		
		# Check that report IDs are different
		self.assertNotEqual(report_card1.report_id, report_card2.report_id)
	
	def test_html_content_generation(self):
		"""Test HTML content generation"""
		
		report_card = frappe.new_doc("Student Report Card")
		report_card.student = "TEST-STU-001"
		report_card.academic_year = "2024-25"
		report_card.student_group = "Test Class 2024"
		report_card.insert()
		
		# Check HTML content structure
		html = report_card.html_content
		self.assertIn("<!DOCTYPE html>", html)
		self.assertIn("Student Report Card", html)
		self.assertIn("Test Student", html)
		self.assertIn("QR Code", html)
	
	def test_qr_code_generation(self):
		"""Test QR code generation"""
		
		report_card = frappe.new_doc("Student Report Card")
		report_card.student = "TEST-STU-001"
		report_card.academic_year = "2024-25"
		report_card.student_group = "Test Class 2024"
		report_card.insert()
		
		# Test QR code base64 generation
		qr_base64 = report_card.generate_qr_code_base64()
		self.assertIsNotNone(qr_base64)
		self.assertTrue(len(qr_base64) > 0)
	
	def tearDown(self):
		"""Clean up test data"""
		
		# Delete test report cards
		frappe.db.sql("DELETE FROM `tabStudent Report Card` WHERE student = 'TEST-STU-001'")
		
		# Delete test student group
		if frappe.db.exists("Student Group", "Test Class 2024"):
			frappe.delete_doc("Student Group", "Test Class 2024")
		
		# Delete test student
		if frappe.db.exists("Student", "TEST-STU-001"):
			frappe.delete_doc("Student", "TEST-STU-001")
		
		# Delete test program
		if frappe.db.exists("Program", "Test Program"):
			frappe.delete_doc("Program", "Test Program")
		
		# Delete test academic year
		if frappe.db.exists("Academic Year", "2024-25"):
			frappe.delete_doc("Academic Year", "2024-25")
		
		frappe.db.commit() 