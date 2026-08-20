# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from education.education.doctype.student_applicant_group_settings.student_applicant_group_settings import (
	is_student_group_open,
)


class TestStudentApplicantGroupSettings(FrappeTestCase):
	def test_group_without_record_is_open(self):
		is_open, message = is_student_group_open("__No Such Group__", "__No Such Year__")
		self.assertTrue(is_open)
		self.assertIsNone(message)
