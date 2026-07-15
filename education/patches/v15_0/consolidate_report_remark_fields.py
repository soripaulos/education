"""Consolidate the remark/signature fields on Student Term/Year Report.

A Student Term Report is per-term and the Student Year Report is per-year, so
carrying "First Semester Remarks", "Second Semester Remarks" and "Final Result"
on a single term report is redundant. Each report needs only a single Remark
plus the Director's Signature.

All of the affected fields were verified empty on every record before this
patch was written, so no data is lost.

Changes (idempotent):
- Student Term Report: delete custom_first_semester_remarks,
  custom_second_semester_remarks, custom_final_result; make
  custom_director_signature a Signature field; add custom_director (name of
  the signatory).
- Student Year Report: add custom_director_signature (Signature) and
  custom_director; it already has custom_remark.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

REMOVE_FROM_TERM = [
	"custom_first_semester_remarks",
	"custom_second_semester_remarks",
	"custom_final_result",
]


def execute():
	# 1) Remove the redundant term-report fields.
	for fieldname in REMOVE_FROM_TERM:
		cf = f"Student Term Report-{fieldname}"
		if frappe.db.exists("Custom Field", cf):
			frappe.delete_doc("Custom Field", cf, ignore_permissions=True, force=True)

	# 2) Make the term-report director signature a real Signature field, and
	#    allow it to be filled in after the report is submitted (so reports can
	#    be bulk-signed whether they are still drafts or already submitted).
	term_sig = "Student Term Report-custom_director_signature"
	if frappe.db.exists("Custom Field", term_sig):
		doc = frappe.get_doc("Custom Field", term_sig)
		doc.fieldtype = "Signature"
		doc.allow_on_submit = 1
		doc.save(ignore_permissions=True)

	# 3) Add the shared fields (idempotent - create_custom_fields skips existing).
	create_custom_fields(
		{
			"Student Term Report": [
				{
					"fieldname": "custom_director",
					"label": "Director",
					"fieldtype": "Link",
					"options": "School Director",
					"insert_after": "custom_remark",
					"read_only": 1,
					"allow_on_submit": 1,
				},
			],
			"Student Year Report": [
				{
					"fieldname": "custom_director",
					"label": "Director",
					"fieldtype": "Link",
					"options": "School Director",
					"insert_after": "custom_remark",
					"read_only": 1,
					"allow_on_submit": 1,
				},
				{
					"fieldname": "custom_director_signature",
					"label": "Director Signature",
					"fieldtype": "Signature",
					"insert_after": "custom_director",
					"read_only": 1,
					"allow_on_submit": 1,
				},
			],
		},
		ignore_validate=True,
	)
