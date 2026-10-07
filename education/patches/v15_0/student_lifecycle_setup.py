"""Prepare existing records for the student lifecycle tools.

* Creates the Section / Student Applicant fields on Program Enrollment and
  the Branch field on Student Group (fixtures sync after patches, so this
  cannot wait for them).
* Gives every section a branch: second-branch sections have always carried
  "Branch" in their name; everything else is the main campus.
* Writes each student's current section onto their enrollment for the year
  that section serves. Sections are rolled over to the next year by name, so
  this is what keeps "who was in Grade 3 B in 2018" answerable afterwards.
* Links each enrollment to the application it came from, where one exists
  for the same School ID and year.
* Fills the fallback promotion pass mark in Education Settings (60).

Everything only fills blanks, so the patch is safe to re-run.
"""

import frappe

from education.education.lifecycle.common import branch_of_section
from education.education.lifecycle.groups import archive_sections
from education.education.lifecycle.setup import make_custom_fields


def execute():
	make_custom_fields()
	frappe.clear_cache(doctype="Program Enrollment")
	frappe.clear_cache(doctype="Student Group")

	for name in frappe.get_all("Student Group", filters={"branch": ["is", "not set"]}, pluck="name"):
		frappe.db.set_value("Student Group", name, "branch", branch_of_section(name), update_modified=False)

	years = frappe.get_all(
		"Student Group", filters={"academic_year": ["is", "set"]}, pluck="academic_year", distinct=True
	)
	for year in years:
		archive_sections(year)

	frappe.db.sql(
		"""
		UPDATE `tabProgram Enrollment` pe
		JOIN `tabStudent` s ON s.name = pe.student
		JOIN `tabStudent Applicant` sa
		  ON sa.custom_school_id = s.custom_school_id
		 AND sa.academic_year = pe.academic_year
		 AND sa.application_status != 'Rejected'
		SET pe.student_applicant = sa.name
		WHERE IFNULL(pe.student_applicant, '') = ''
		"""
	)

	if frappe.get_meta("Education Settings").has_field("promotion_pass_mark"):
		if not frappe.db.get_single_value("Education Settings", "promotion_pass_mark"):
			frappe.db.set_single_value("Education Settings", "promotion_pass_mark", 60)
