"""Fields the lifecycle tools add to existing doctypes.

Created from code (on install, on every migrate, and by the backfill patch)
rather than fixtures, because fixtures are synced after patches run and the
backfill needs these columns to exist first.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

BRANCH_OPTIONS = "\nMain\nMBS #2\nMBS Dembi Dollo"

CUSTOM_FIELDS = {
	"Program Enrollment": [
		{
			"fieldname": "student_group",
			"label": "Section",
			"fieldtype": "Link",
			"options": "Student Group",
			"insert_after": "student_batch_name",
			"in_standard_filter": 1,
			"search_index": 1,
			"description": "The section (Student Group) the student sits in for this academic year. Kept here permanently, so it survives the section being rolled over to a later year.",
		},
		{
			"fieldname": "student_applicant",
			"label": "Student Applicant",
			"fieldtype": "Link",
			"options": "Student Applicant",
			"insert_after": "student_group",
			"no_copy": 1,
			"description": "The application this enrollment was made from.",
		},
	],
	"Student Group": [
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Select",
			"options": BRANCH_OPTIONS,
			"insert_after": "program",
			"in_standard_filter": 1,
			"description": "Campus this section is taught at. Used to keep students in sections of their own branch.",
		},
	],
}


def make_custom_fields():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True, update=True)


def get_setting(fieldname, default=None):
	"""An Education Settings value that may not exist yet (before migrate)."""
	if not frappe.get_meta("Education Settings").has_field(fieldname):
		return default
	value = frappe.db.get_single_value("Education Settings", fieldname)
	return default if value in (None, "") else value
