"""Allow one Student Applicant record per student per academic year.

Student Applicant carried UNIQUE indexes on both `custom_school_id` and
`student_email_id`. That made a returning student's yearly re-registration
impossible: inserting a second row for the same School ID raised
UniqueValidationError ("Duplicate entry 'M1/6991/15@m.b.s'").

A student legitimately has one application per academic year, so both columns
must allow repeats. The uniqueness that actually matters - one application per
School ID *per academic year* - is enforced in
`education.education.api.submit_existing_student_application`, which refreshes
the current year's record in place instead of creating a duplicate.

New-student School IDs stay collision-free: `generate_school_id` /
`generate_dd_school_id` explicitly check both Student and Student Applicant for
an existing ID before returning one.

The doctype JSON no longer declares `unique: 1`, so model sync may already have
dropped these indexes by the time this runs (it is a post_model_sync patch).
Everything below is guarded and idempotent, and drops the indexes explicitly in
case the schema sync left them in place.

A plain (non-unique) index on custom_school_id is kept, because both the
registration pages and the staff dashboards look applicants up by School ID.
"""

import frappe

TABLE = "tabStudent Applicant"


def _index_rows(index_name):
	return frappe.db.sql(
		f"SHOW INDEX FROM `{TABLE}` WHERE Key_name=%s", (index_name,), as_dict=True
	)


def execute():
	if not frappe.db.table_exists("Student Applicant"):
		return

	# 1) Drop the unique indexes if they are still unique.
	for index_name in ("custom_school_id", "student_email_id"):
		rows = _index_rows(index_name)
		if rows and rows[0].get("Non_unique") == 0:
			frappe.db.sql_ddl(f"ALTER TABLE `{TABLE}` DROP INDEX `{index_name}`")

	# 2) Re-add a non-unique index on custom_school_id for lookups.
	if not _index_rows("custom_school_id"):
		frappe.db.sql_ddl(
			f"ALTER TABLE `{TABLE}` ADD INDEX `custom_school_id` (`custom_school_id`)"
		)
