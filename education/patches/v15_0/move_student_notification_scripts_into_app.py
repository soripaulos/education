import frappe
from frappe.utils import add_days, now_datetime

# These site Server Scripts now live in the app (education/education/
# notification_triggers.py and App Notification.validate). Left enabled they
# would notify every family twice.
REPLACED_SCRIPTS = [
	"Teacher Parent Message - Notify Student on Creation",
	"Student Hub Evaluation - Notify Student on Creation",
	"Student Incident - Notify Student on Creation",
	"Appeal Result - Notify Student on Resolution",
	"Fix App Notification Target",
]


def execute():
	for name in REPLACED_SCRIPTS:
		if frappe.db.exists("Server Script", name):
			frappe.db.set_value("Server Script", name, "disabled", 1)

	backfill_inboxes()


def backfill_inboxes():
	"""Give each student an inbox entry for notifications sent before the inbox existed.

	Anything older than a week is marked read so families do not open the app
	to a wall of old alerts.
	"""
	from education.education.doctype.app_notification.app_notification import update_delivery_summary

	cutoff = add_days(now_datetime(), -7)
	sent = frappe.get_all(
		"App Notification",
		filters={"docstatus": 1},
		fields=["name", "title", "message", "notification_category", "sent_date", "creation"],
	)
	for n in sent:
		if frappe.db.exists("Student Notification", {"notification": n.name}):
			continue
		doc = frappe.get_doc("App Notification", n.name)
		students = doc.get_recipient_students()
		if not students:
			continue
		info = {
			s.name: s
			for s in frappe.get_all(
				"Student", filters={"name": ("in", students)}, fields=["name", "student_name", "user"]
			)
		}
		sent_on = n.sent_date or n.creation
		is_read = 1 if sent_on < cutoff else 0
		values = []
		for student in students:
			s = info.get(student)
			if not s:
				continue
			values.append((
				frappe.generate_hash(length=12), sent_on, sent_on, "Administrator", "Administrator", 0,
				student, s.student_name, s.user, n.name, n.title, n.message, n.notification_category,
				sent_on, is_read, "Not Tracked",
			))
		frappe.db.bulk_insert(
			"Student Notification",
			fields=[
				"name", "creation", "modified", "owner", "modified_by", "docstatus",
				"student", "student_name", "user", "notification", "title", "message", "category",
				"sent_on", "is_read", "push_status",
			],
			values=values,
		)
		update_delivery_summary(n.name)
