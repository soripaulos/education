# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentApplicantGroupSettings(Document):
	def validate(self):
		self.validate_unique_group_year()

	def validate_unique_group_year(self):
		# One settings record per student group + academic year combination
		existing = frappe.db.get_value(
			"Student Applicant Group Settings",
			{
				"student_group": self.student_group,
				"academic_year": self.academic_year,
				"name": ("!=", self.name),
			},
			"name",
		)
		if existing:
			frappe.throw(
				_(
					"Settings for Student Group {0} in Academic Year {1} already exist: {2}"
				).format(self.student_group, self.academic_year, existing)
			)


def is_student_group_open(student_group, academic_year):
	"""Return (is_open, closed_message) for a group/year pair.

	Groups without a settings record are open by default, so applications keep
	working until someone explicitly closes them.
	"""
	settings = frappe.db.get_value(
		"Student Applicant Group Settings",
		{"student_group": student_group, "academic_year": academic_year},
		["allow_new_applicants", "closed_message"],
		as_dict=True,
	)
	if not settings:
		return True, None
	if settings.allow_new_applicants:
		return True, None
	return False, settings.closed_message
