# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Events that notify a student's family, all in one place.

These used to be Server Scripts on the site ("... - Notify Student on
Creation", "Appeal Result - Notify Student on Resolution"); the patch
`move_student_notification_scripts_into_app` disables those so nothing is
sent twice. Every notification goes through `notify_student`, which creates
an App Notification addressed to exactly one student, so it lands only in
that student's inbox and on the phones signed in to that student's account.
"""

import frappe
from frappe.utils import formatdate, strip_html, today


def notify_student(student, title, message, category, reference_doctype=None, reference_name=None):
	"""Send one notification to one student (their inbox + their phones)."""
	if not student:
		return None
	info = frappe.db.get_value("Student", student, ["student_name", "student_email_id"], as_dict=True)
	if not info:
		return None

	notif = frappe.new_doc("App Notification")
	notif.naming_series = "APP-NOTIF-.YYYY.-"
	notif.title = title[:140]
	notif.notification_category = category
	notif.message = message
	notif.send_to_all_students = 0
	notif.reference_doctype = reference_doctype
	notif.reference_name = reference_name
	notif.append("students", {
		"student": student,
		"student_name": info.student_name,
		"student_email": info.student_email_id or "",
	})
	try:
		# A savepoint so a failure here never undoes the teacher's message,
		# incident report, etc. that triggered it.
		frappe.db.savepoint("notify_student")
		notif.insert(ignore_permissions=True)
		notif.submit()
		return notif.name
	except Exception:
		frappe.db.rollback(save_point="notify_student")
		frappe.log_error(frappe.get_traceback(), f"Could not notify student {student}")
		return None


def _student_name(student):
	return frappe.db.get_value("Student", student, "student_name") or student


def _short(text, length=200):
	text = strip_html(text or "").strip()
	return text if len(text) <= length else text[: length - 1] + "…"


# ----------------------------------------------------------------------
# Teacher Parent Message
# ----------------------------------------------------------------------

def teacher_parent_message_after_insert(doc, method=None):
	subject = doc.subject or "New Message"
	date = formatdate(doc.message_date) if doc.message_date else formatdate(today())
	message = (
		"A new message has been sent to " + _student_name(doc.student) + " by their teacher.\n\n"
		"Subject: " + subject + "\n"
		"Date: " + date + "\n\n"
		"Please review the message in your portal."
	)
	notify_student(doc.student, "Teacher Message: " + subject, message, "General", doc.doctype, doc.name)


def teacher_parent_message_on_update(doc, method=None):
	before = doc.get_doc_before_save()
	if not before:
		return
	subject = doc.subject or "your message"

	# Teacher replied: tell the family.
	teacher_replies = _new_entries(before, doc, "Teacher")
	if doc.teacher_followup and not before.teacher_followup:
		teacher_replies.insert(0, doc.teacher_followup)
	if teacher_replies:
		notify_student(
			doc.student,
			"Teacher replied: " + subject,
			_short(teacher_replies[-1]),
			"General",
			doc.doctype,
			doc.name,
		)

	# Family replied: tell the teacher in their staff app inbox.
	parent_replies = _new_entries(before, doc, "Parent")
	if doc.parent_response and not before.parent_response:
		parent_replies.insert(0, doc.parent_response)
	if parent_replies and doc.teacher:
		_notify_teacher(doc, _short(parent_replies[-1]))

	# The family opened the message: clear its unread alerts too.
	if doc.status in ("Read", "Responded") and before.status == "Unread":
		from education.api.student_inbox import mark_read_for_reference

		mark_read_for_reference(doc.doctype, doc.name)


def _new_entries(before, doc, sender_type):
	"""Conversation entries from `sender_type` added in this save."""
	if not doc.meta.has_field("custom_conversation"):
		return []
	old = {row.name for row in before.get("custom_conversation") or []}
	return [
		row.content
		for row in doc.get("custom_conversation") or []
		if row.name not in old and row.sender_type == sender_type and row.content
	]


def _notify_teacher(doc, text):
	if not frappe.db.exists("User", doc.teacher):
		return
	frappe.get_doc({
		"doctype": "Notification Log",
		"for_user": doc.teacher,
		"type": "Alert",
		"document_type": doc.doctype,
		"document_name": doc.name,
		"subject": "Parent of " + _student_name(doc.student) + " replied: " + (doc.subject or ""),
		"email_content": text,
	}).insert(ignore_permissions=True)


# ----------------------------------------------------------------------
# Student Hub Evaluation / Student Discipline Incident / Appeal Result
# ----------------------------------------------------------------------

def hub_evaluation_after_insert(doc, method=None):
	review_date = formatdate(doc.get("review_date")) if doc.get("review_date") else formatdate(today())
	message = (
		"A new performance evaluation has been posted for " + _student_name(doc.student) + ".\n\n"
		"Date: " + review_date + "\n\n"
		"Please review your evaluation in the Student Hub."
	)
	notify_student(doc.student, "New Evaluation Posted — " + review_date, message, "Academic", doc.doctype, doc.name)


def discipline_incident_after_insert(doc, method=None):
	incident_type = doc.get("incident_type") or "Incident"
	severity = doc.get("severity") or "Medium"
	incident_date = formatdate(doc.get("incident_date")) if doc.get("incident_date") else formatdate(today())
	message = (
		"An incident report has been filed against " + _student_name(doc.student) + ".\n\n"
		"Incident Type: " + incident_type + "\n"
		"Date: " + incident_date + "\n"
		"Severity: " + severity + "\n"
		"Status: " + (doc.get("status") or "") + "\n\n"
		"Please open the incident log to review the details and submit your response."
	)
	notify_student(
		doc.student, "Incident Report: " + incident_type + " — " + incident_date, message, "Urgent", doc.doctype, doc.name
	)


def appeal_result_on_update(doc, method=None):
	"""Tell the student once when their appeal is resolved or rejected."""
	before = doc.get_doc_before_save()
	if not before or before.status == doc.status:
		return
	if doc.status not in ("Resolved", "Rejected") or not doc.get("resolution"):
		return
	subject = doc.get("subject") or "your subject"
	exam = doc.get("exam") or "the exam"
	message = (
		"Your appeal for " + str(subject) + " (" + str(exam) + ") "
		"has been " + str(doc.status).lower() + ".\n\n"
		"Resolution: " + doc.resolution
	)
	notify_student(
		doc.student, "Appeal " + str(doc.status) + ": " + str(subject), message, "Academic", doc.doctype, doc.name
	)
