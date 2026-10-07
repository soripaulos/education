# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The student app's inbox.

Every call works on the signed-in account's own student only. There is no
way to ask for another student's inbox, which is what keeps families apart.
"""

import frappe
from frappe import _
from frappe.utils import cint, now

INBOX_FIELDS = [
	"name", "title", "message", "category", "sent_on", "is_read", "read_on",
	"notification", "reference_doctype", "reference_name", "student", "student_name",
]


def _my_student():
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)
	student = frappe.db.get_value("Student", {"user": user}, ["name", "student_name"], as_dict=True)
	if not student:
		frappe.throw(_("This login is not linked to a student"), frappe.PermissionError)
	return student


@frappe.whitelist()
def get_inbox(limit=30, offset=0, category=None, unread_only=0):
	"""This student's notifications, newest first, with the unread count."""
	student = _my_student()
	filters = {"student": student.name}
	if category and category != "All":
		filters["category"] = category
	if cint(unread_only):
		filters["is_read"] = 0

	items = frappe.get_all(
		"Student Notification",
		filters=filters,
		fields=INBOX_FIELDS,
		order_by="sent_on desc, creation desc",
		limit_start=cint(offset),
		limit_page_length=min(cint(limit) or 30, 200),
		ignore_permissions=True,
	)
	return {
		"student": student.name,
		"student_name": student.student_name,
		"items": items,
		"unread_count": _unread(student.name),
	}


@frappe.whitelist()
def get_unread_count():
	return {"unread_count": _unread(_my_student().name)}


@frappe.whitelist()
def mark_read(names=None):
	"""Mark some of this student's notifications read. `names` is a list or JSON list."""
	student = _my_student()
	names = frappe.parse_json(names) if isinstance(names, str) else names
	if not names:
		return {"unread_count": _unread(student.name)}
	rows = frappe.get_all(
		"Student Notification",
		filters={"name": ("in", names), "student": student.name, "is_read": 0},
		fields=["name", "notification", "reference_doctype", "reference_name"],
		ignore_permissions=True,
	)
	_set_read(rows)
	return {"unread_count": _unread(student.name)}


@frappe.whitelist()
def mark_all_read():
	student = _my_student()
	rows = frappe.get_all(
		"Student Notification",
		filters={"student": student.name, "is_read": 0},
		fields=["name", "notification", "reference_doctype", "reference_name"],
		limit_page_length=0,
		ignore_permissions=True,
	)
	_set_read(rows)
	return {"unread_count": 0}


def _unread(student):
	return frappe.db.count("Student Notification", {"student": student, "is_read": 0})


def _set_read(rows):
	if not rows:
		return
	stamp = now()
	frappe.db.set_value(
		"Student Notification",
		{"name": ("in", [r.name for r in rows])},
		{"is_read": 1, "read_on": stamp},
		update_modified=False,
	)
	# Reading the alert about a teacher's message counts as seeing the
	# message, so the teacher sees "Seen" in the staff app.
	for r in rows:
		if r.reference_doctype == "Teacher Parent Message" and r.reference_name:
			if frappe.db.get_value("Teacher Parent Message", r.reference_name, "status") == "Unread":
				frappe.db.set_value("Teacher Parent Message", r.reference_name, "status", "Read")
	refresh_read_counts({r.notification for r in rows if r.notification})


def refresh_read_counts(notifications):
	from education.education.doctype.app_notification.app_notification import update_delivery_summary

	for name in notifications:
		update_delivery_summary(name)


def mark_read_for_reference(doctype, name):
	"""Someone opened the record itself (e.g. the message in the Hub): clear its alerts."""
	rows = frappe.get_all(
		"Student Notification",
		filters={"reference_doctype": doctype, "reference_name": name, "is_read": 0},
		fields=["name", "notification", "reference_doctype", "reference_name"],
		ignore_permissions=True,
	)
	if rows:
		frappe.db.set_value(
			"Student Notification",
			{"name": ("in", [r.name for r in rows])},
			{"is_read": 1, "read_on": now()},
			update_modified=False,
		)
		refresh_read_counts({r.notification for r in rows if r.notification})
