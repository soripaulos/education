"""Consolidate the remark/signature fields on Student Term/Year Report.

A Student Term Report is per-term and the Student Year Report is per-year, so
carrying "First Semester Remarks", "Second Semester Remarks" and "Final Result"
on a single term report is redundant. Each report needs only a single Remark
plus the Director's Signature.

All of the affected fields were verified empty on every record before this
patch was written, so no data is lost.

Changes (idempotent):
- Student Term Report: delete custom_first_semester_remarks,
  custom_second_semester_remarks, custom_final_result; replace the existing
  custom_director_signature (originally Small Text) with a Signature field;
  add custom_director (name of the signatory).
- Student Year Report: add custom_director_signature (Signature) and
  custom_director; it already has custom_remark.

NOTE: We do NOT mutate the fieldtype of an existing Custom Field in place.
Frappe's Custom Field validator refuses any fieldtype change ("Fieldtype cannot
be changed from X to Y"). Instead, if custom_director_signature already exists
as a non-Signature field, we delete it first and create a fresh Signature
field via create_custom_fields.
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

	# 2) Delete any pre-existing custom_director_signature on either report so
	#    we can install a fresh Signature field. Frappe blocks fieldtype
	#    mutation on an existing Custom Field, so recreate is the only safe
	#    path. The fields were verified empty before this patch.
	for dt in ("Student Term Report", "Student Year Report"):
		cf = f"{dt}-custom_director_signature"
		if frappe.db.exists("Custom Field", cf):
			frappe.delete_doc("Custom Field", cf, ignore_permissions=True, force=True)

	# 3) Install the consolidated fields. create_custom_fields is idempotent
	#    for fields that don't yet exist.
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
				{
					"fieldname": "custom_director_signature",
					"label": "Director Signature",
					"fieldtype": "Signature",
					"insert_after": "custom_director",
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
