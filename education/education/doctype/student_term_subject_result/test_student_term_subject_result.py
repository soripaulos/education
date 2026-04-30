# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import today, add_days


class TestStudentTermSubjectResult(unittest.TestCase):
	def setUp(self):
		"""Set up test data"""
		self.academic_year = self.create_test_academic_year()
		self.academic_term = self.create_test_academic_term()
		self.student = self.create_test_student()
		self.student_group = self.create_test_student_group()
		self.course = self.create_test_course()
		self.assessment_criteria = self.create_test_assessment_criteria()
		self.program = self.create_test_program()

	def create_test_academic_year(self):
		"""Create a test academic year"""
		if not frappe.db.exists("Academic Year", "2024-25"):
			doc = frappe.get_doc({
				"doctype": "Academic Year",
				"academic_year_name": "2024-25",
				"year_start_date": "2024-04-01",
				"year_end_date": "2025-03-31"
			})
			doc.insert()
		return "2024-25"

	def create_test_academic_term(self):
		"""Create a test academic term"""
		if not frappe.db.exists("Academic Term", "Term 1 2024-25"):
			doc = frappe.get_doc({
				"doctype": "Academic Term",
				"academic_year": self.academic_year,
				"term_name": "Term 1",
				"term_start_date": "2024-04-01",
				"term_end_date": "2024-09-30"
			})
			doc.insert()
		return "Term 1 2024-25"

	def create_test_student(self):
		"""Create a test student"""
		if not frappe.db.exists("Student", {"student_email_id": "test.student@example.com"}):
			doc = frappe.get_doc({
				"doctype": "Student",
				"first_name": "Test",
				"last_name": "Student",
				"student_email_id": "test.student@example.com",
				"joining_date": today()
			})
			doc.insert()
			return doc.name
		else:
			return frappe.db.get_value("Student", {"student_email_id": "test.student@example.com"}, "name")

	def create_test_student_group(self):
		"""Create a test student group"""
		if not frappe.db.exists("Student Group", "Test Group"):
			doc = frappe.get_doc({
				"doctype": "Student Group",
				"student_group_name": "Test Group",
				"academic_year": self.academic_year,
				"academic_term": self.academic_term,
				"program": self.program
			})
			doc.insert()
		return "Test Group"

	def create_test_course(self):
		"""Create a test course"""
		if not frappe.db.exists("Course", "Test Mathematics"):
			doc = frappe.get_doc({
				"doctype": "Course",
				"course_name": "Test Mathematics",
				"course_code": "MATH101"
			})
			doc.insert()
		return "Test Mathematics"

	def create_test_assessment_criteria(self):
		"""Create a test assessment criteria"""
		if not frappe.db.exists("Assessment Criteria", "Test Midterm"):
			doc = frappe.get_doc({
				"doctype": "Assessment Criteria",
				"assessment_criteria": "Test Midterm",
				"maximum_score": 100
			})
			doc.insert()
		return "Test Midterm"

	def create_test_program(self):
		"""Create a test program"""
		if not frappe.db.exists("Program", "Test Program"):
			doc = frappe.get_doc({
				"doctype": "Program",
				"program_name": "Test Program",
				"program_code": "TEST"
			})
			doc.insert()
		return "Test Program"

	def test_create_result(self):
		"""Test creating a student term subject result"""
		doc = frappe.get_doc({
			"doctype": "Student Term Subject Result",
			"student": self.student,
			"academic_year": self.academic_year,
			"academic_term": self.academic_term,
			"subject": self.course,
			"student_group": self.student_group,
			"grade": self.program,
			"assessment_criteria": self.assessment_criteria,
			"score": 85,
			"maximum_score": 100
		})
		doc.insert()
		
		# Test percentage calculation
		self.assertEqual(doc.percentage, 85.0)
		
		# Test submission
		doc.submit()
		self.assertEqual(doc.docstatus, 1)

	def test_duplicate_prevention(self):
		"""Test that duplicate results are prevented"""
		# Create first result
		doc1 = frappe.get_doc({
			"doctype": "Student Term Subject Result",
			"student": self.student,
			"academic_year": self.academic_year,
			"academic_term": self.academic_term,
			"subject": self.course,
			"student_group": self.student_group,
			"grade": self.program,
			"assessment_criteria": self.assessment_criteria,
			"score": 85,
			"maximum_score": 100
		})
		doc1.insert()
		
		# Try to create duplicate
		doc2 = frappe.get_doc({
			"doctype": "Student Term Subject Result",
			"student": self.student,
			"academic_year": self.academic_year,
			"academic_term": self.academic_term,
			"subject": self.course,
			"student_group": self.student_group,
			"grade": self.program,
			"assessment_criteria": self.assessment_criteria,
			"score": 90,
			"maximum_score": 100
		})
		
		with self.assertRaises(frappe.ValidationError):
			doc2.insert()

	def test_score_validation(self):
		"""Test score validation"""
		# Test score exceeding maximum
		doc = frappe.get_doc({
			"doctype": "Student Term Subject Result",
			"student": self.student,
			"academic_year": self.academic_year,
			"academic_term": self.academic_term,
			"subject": self.course,
			"student_group": self.student_group,
			"grade": self.program,
			"assessment_criteria": self.assessment_criteria,
			"score": 110,
			"maximum_score": 100
		})
		
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def tearDown(self):
		"""Clean up test data"""
		# Delete test results
		frappe.db.delete("Student Term Subject Result", {
			"student": self.student,
			"academic_year": self.academic_year
		})
		frappe.db.commit() 