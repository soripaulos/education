"""What leaving the school, and coming back, does to a student's records.

A submitted Student Exit is the single place a departure is recorded. When
it is submitted the Student is disabled with its leaving details filled in,
its active section memberships are switched off, and (optionally) its login
is disabled. Everything that was changed is remembered on the exit, so
cancelling it puts the student back exactly as they were.

Coming back is a readmission: enrolling a student who has an open exit
re-enables them and marks the exit "Readmitted" rather than deleting it, so
the history of the gap survives.
"""

import json

import frappe
from frappe import _
from frappe.utils import getdate, today

STUDENT_EXIT = "Student Exit"

# Student fields an exit writes, remembered so a cancel can restore them.
STUDENT_FIELDS = (
	"enabled",
	"date_of_leaving",
	"leaving_certificate_number",
	"reason_for_leaving",
	"custom_reason_for_leaving_copy",
	"custom_exams_taken",
)


def exit_doctype_ready():
	return frappe.db.table_exists(STUDENT_EXIT)


def open_exits(student):
	"""Submitted exits for ``student`` that have not been undone by readmission."""
	if not exit_doctype_ready():
		return []
	return frappe.get_all(
		STUDENT_EXIT,
		filters={"student": student, "docstatus": 1, "status": "Exited"},
		fields=["name", "exit_type", "exit_date", "applied_changes"],
		order_by="exit_date desc",
	)


def log_change(student, activity_type, description, reference_doctype=None, reference_name=None):
	"""Write a Student Data Change Log entry when that log exists on the site.

	Changes made with direct database writes do not pass through the hooks
	that normally record them, so they are logged here explicitly.
	"""
	if not frappe.db.table_exists("Student Data Change Log"):
		return
	meta = frappe.get_meta("Student Data Change Log")
	options = (meta.get_field("activity_type").options or "").split("\n")
	if activity_type not in options:
		activity_type = "Manual Entry" if "Manual Entry" in options else options[-1]
	try:
		entry = frappe.new_doc("Student Data Change Log")
		entry.student = student
		entry.activity_category = "Enrollment"
		entry.activity_type = activity_type
		entry.change_description = description
		entry.source = "Auto"
		entry.reference_doctype = reference_doctype
		entry.reference_name = reference_name
		entry.changed_by = frappe.session.user
		entry.changed_on = frappe.utils.now()
		entry.flags.ignore_permissions = True
		entry.insert(ignore_permissions=True)
	except Exception:
		# The audit log is a convenience; it must never undo the change it
		# describes.
		frappe.log_error(frappe.get_traceback(), "Student lifecycle: change log entry failed")


def _set_select(student, fieldname, value):
	"""Set a Select field only when ``value`` is one of its options."""
	field = student.meta.get_field(fieldname)
	if not field or not value:
		return
	options = (field.options or "").split("\n")
	if field.fieldtype != "Select" or value in options:
		student.set(fieldname, value)


def apply_exit(exit_doc):
	"""Carry a submitted exit onto the Student, its sections and its login."""
	student = frappe.get_doc("Student", exit_doc.student)
	changes = {"student": {f: student.get(f) for f in STUDENT_FIELDS if student.meta.has_field(f)}}

	student.enabled = 0
	student.date_of_leaving = exit_doc.exit_date
	if exit_doc.leaving_certificate_number:
		student.leaving_certificate_number = exit_doc.leaving_certificate_number
	_set_select(student, "custom_reason_for_leaving_copy", exit_doc.reason_for_leaving)
	_set_select(student, "custom_exams_taken", exit_doc.last_exams_taken)
	student.reason_for_leaving = exit_doc.reason_details or exit_doc.exit_type
	student.flags.skip_user_creation = True
	student.flags.ignore_permissions = True
	student.save()

	changes["memberships"] = []
	if exit_doc.deactivate_group_membership:
		rows = frappe.get_all(
			"Student Group Student",
			filters={"student": exit_doc.student, "active": 1, "parenttype": "Student Group"},
			fields=["name", "parent"],
		)
		for row in rows:
			frappe.db.set_value("Student Group Student", row.name, "active", 0)
			changes["memberships"].append([row.name, row.parent])
			log_change(
				exit_doc.student,
				"Student Group Active Changed",
				_("Marked inactive in {0} ({1} {2})").format(row.parent, exit_doc.doctype, exit_doc.name),
				exit_doc.doctype,
				exit_doc.name,
			)

	changes["user_disabled"] = ""
	if exit_doc.disable_user_login and student.user:
		if frappe.db.get_value("User", student.user, "enabled"):
			_set_user_enabled(student.user, 0)
			changes["user_disabled"] = student.user

	exit_doc.db_set("applied_changes", json.dumps(changes, default=str), update_modified=False)


def revert_exit(exit_doc):
	"""Undo :func:`apply_exit` for a cancelled exit that was never readmitted."""
	changes = json.loads(exit_doc.applied_changes or "{}")
	student = frappe.get_doc("Student", exit_doc.student)

	other_open = [e for e in open_exits(exit_doc.student) if e.name != exit_doc.name]
	if not other_open:
		for fieldname, value in (changes.get("student") or {}).items():
			if student.meta.has_field(fieldname):
				student.set(fieldname, value)
		if "enabled" not in (changes.get("student") or {}):
			student.enabled = 1
			student.date_of_leaving = None
		student.flags.skip_user_creation = True
		student.flags.ignore_permissions = True
		student.save()

	for row_name, parent in changes.get("memberships") or []:
		if frappe.db.exists("Student Group Student", row_name):
			frappe.db.set_value("Student Group Student", row_name, "active", 1)
			log_change(
				exit_doc.student,
				"Student Group Active Changed",
				_("Re-activated in {0} (cancelled {1})").format(parent, exit_doc.name),
				exit_doc.doctype,
				exit_doc.name,
			)

	user = changes.get("user_disabled")
	if user and not other_open and frappe.db.exists("User", user):
		_set_user_enabled(user, 1)


def readmit(student_name, enrollment=None):
	"""Re-enable a returning student and close their open exits.

	Returns the names of the exits that were marked Readmitted.
	"""
	exits = open_exits(student_name)
	student = frappe.get_doc("Student", student_name)
	if not student.enabled or student.date_of_leaving:
		student.enabled = 1
		student.date_of_leaving = None
		student.flags.skip_user_creation = True
		student.flags.ignore_permissions = True
		student.save()

	for row in exits:
		frappe.db.set_value(
			STUDENT_EXIT,
			row.name,
			{"status": "Readmitted", "readmitted_on": today(), "readmission_enrollment": enrollment},
		)
		changes = json.loads(row.applied_changes or "{}")
		user = changes.get("user_disabled")
		if user and frappe.db.exists("User", user) and not frappe.db.get_value("User", user, "enabled"):
			_set_user_enabled(user, 1)
	return [row.name for row in exits]


def _set_user_enabled(user, enabled):
	"""Enable/disable a login through the document, so sessions are handled."""
	try:
		doc = frappe.get_doc("User", user)
		doc.enabled = enabled
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
	except Exception:
		frappe.db.set_value("User", user, "enabled", enabled)
		frappe.clear_cache(user=user)
		frappe.log_error(frappe.get_traceback(), f"Student lifecycle: could not update User {user}")


def make_exit(
	student,
	exit_type,
	exit_date=None,
	academic_year=None,
	program=None,
	student_group=None,
	reason_details=None,
	disable_user_login=1,
	submit=True,
):
	"""Create (and by default submit) a Student Exit from code."""
	doc = frappe.new_doc(STUDENT_EXIT)
	doc.student = student
	doc.exit_type = exit_type
	doc.exit_date = getdate(exit_date or today())
	doc.academic_year = academic_year
	doc.program = program
	doc.student_group = student_group
	doc.reason_details = reason_details
	doc.disable_user_login = 1 if disable_user_login else 0
	doc.deactivate_group_membership = 1
	doc.flags.ignore_permissions = True
	doc.insert()
	if submit:
		doc.submit()
	return doc
