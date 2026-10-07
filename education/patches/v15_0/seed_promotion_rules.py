"""Create the starting Promotion Rules (only on a site that has none).

* Default School Rule - every grade without its own rule: not promoted when
  the year average is below the old pass mark (60), or 3+ subjects are below
  50, or 2+ subjects are below 40.
* Grade 6 / Grade 8 Regional Exam - those grades are decided by the result
  written on the External Exam Result.

All of it can be changed or disabled from the Promotion Rule list.
"""

import frappe
from frappe.utils import flt


def execute():
	if not frappe.db.table_exists("Promotion Rule") or frappe.db.count("Promotion Rule"):
		return
	programs = set(frappe.get_all("Program", pluck="name"))

	for grade in ("Grade 6", "Grade 8"):
		rule = frappe.new_doc("Promotion Rule")
		rule.rule_name = f"{grade} Regional Exam"
		rule.decided_by = "External Exam"
		rule.exam_type = f"{grade} Regional Exam"
		for program in (grade, f"{grade} AO"):
			if program in programs:
				rule.append("programs", {"program": program})
		if rule.programs:
			rule.insert(ignore_permissions=True)

	pass_mark = 60
	if frappe.get_meta("Education Settings").has_field("promotion_pass_mark"):
		pass_mark = flt(frappe.db.get_single_value("Education Settings", "promotion_pass_mark")) or 60
	rule = frappe.new_doc("Promotion Rule")
	rule.rule_name = "Default School Rule"
	rule.decided_by = "School Results"
	rule.year_average_below = pass_mark
	rule.append("conditions", {"failed_subjects": 3, "subject_mark_below": 50})
	rule.append("conditions", {"failed_subjects": 2, "subject_mark_below": 40})
	rule.insert(ignore_permissions=True)
