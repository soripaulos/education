# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""School notifications to students and their families.

Submitting an App Notification:
  1. works out exactly which students it is for,
  2. gives each of them their own Student Notification (their inbox entry),
  3. alerts every phone signed in to each student's account.

The student app reads only the signed-in student's inbox entries, so a
family never sees another family's messages. A phone signed in to several
children's accounts is registered under each of them, so it is alerted for
all of them, whichever child is open in the app at the time.
"""

import json
from typing import Any, Dict, List

import frappe
import requests
from frappe.model.document import Document
from frappe.utils import add_to_date, cint, get_datetime, now, now_datetime

EXPO_SEND_URL = "https://exp.host/--/api/v2/push/send"
EXPO_RECEIPTS_URL = "https://exp.host/--/api/v2/push/getReceipts"
# Expo rejects a request with more than 100 messages / 1000 receipt ids.
EXPO_SEND_BATCH = 100
EXPO_RECEIPT_BATCH = 1000


class AppNotification(Document):
    def validate(self):
        """Validate the notification before saving."""
        self.set("students", [row for row in (self.students or []) if row.student])
        self.set("student_groups", [row for row in (self.student_groups or []) if row.student_group])

        # Explicit recipients always win over the broadcast flag. A notification
        # meant for one student must never fan out to the whole school because
        # a client also sent send_to_all_students=1.
        if self.students or self.student_groups:
            self.send_to_all_students = 0

        if not self.send_to_all_students and not self.student_groups and not self.students:
            frappe.throw("Please select at least one recipient (Student Groups or Individual Students) or enable 'Send to All Students'")

    def on_submit(self):
        """Deliver to every recipient's inbox and phones when the document is submitted."""
        self.send_push_notifications()

    def send_push_notifications(self, only_failed=False):
        """Deliver this notification and record the outcome per student.

        Never raises: a failed alert must not roll back the document that
        triggered it (a teacher's parent message, an incident report, ...).
        """
        try:
            if only_failed:
                entries = frappe.get_all(
                    "Student Notification",
                    filters={"notification": self.name, "push_status": "Failed"},
                    fields=["name", "student", "user"],
                )
            else:
                entries = self._create_inbox_entries()

            self._alert_phones(entries)
            self.update(update_delivery_summary(self.name))
            frappe.msgprint(self.delivery_summary)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"App Notification {self.name} failed")
            self.db_set({
                "status": "Failed",
                "delivery_summary": "Sending failed with an unexpected error. See Error Log.",
            })

    # ------------------------------------------------------------------
    # recipients
    # ------------------------------------------------------------------

    def get_recipient_students(self) -> List[str]:
        """The exact list of students this notification is addressed to."""
        if self.send_to_all_students and not self.students and not self.student_groups:
            return frappe.get_all("Student", filters={"enabled": 1}, pluck="name")

        recipients = []
        groups = [row.student_group for row in self.student_groups if row.student_group]
        if groups:
            recipients.extend(
                frappe.get_all(
                    "Student Group Student",
                    filters={"parent": ("in", groups), "active": 1},
                    pluck="student",
                )
            )
        recipients.extend(row.student for row in self.students if row.student)

        # Keep order, drop duplicates.
        return list(dict.fromkeys(recipients))

    def _create_inbox_entries(self) -> List[Dict[str, Any]]:
        """Create one Student Notification per recipient student."""
        frappe.db.delete("Student Notification", {"notification": self.name})

        students = self.get_recipient_students()
        if not students:
            return []

        info = {
            s.name: s
            for s in frappe.get_all(
                "Student",
                filters={"name": ("in", students)},
                fields=["name", "student_name", "user", "enabled"],
            )
        }

        stamp = now()
        owner = frappe.session.user
        fields = [
            "name", "creation", "modified", "owner", "modified_by", "docstatus",
            "student", "student_name", "user", "notification", "reference_doctype", "reference_name",
            "title", "message", "category", "sent_on", "is_read", "push_status", "push_devices", "push_error",
        ]
        values, entries = [], []
        for student in students:
            s = info.get(student)
            if not s:
                continue
            user = s.user if s.enabled else None
            name = frappe.generate_hash(length=12)
            values.append((
                name, stamp, stamp, owner, owner, 0,
                student, s.student_name, s.user, self.name, self.reference_doctype, self.reference_name,
                self.title, self.message, self.notification_category, stamp, 0,
                "Pending" if user else "No Account", 0,
                None if user else "Student has no active app login",
            ))
            entries.append({"name": name, "student": student, "user": user})

        frappe.db.bulk_insert("Student Notification", fields=fields, values=values)
        return entries

    # ------------------------------------------------------------------
    # phone alerts
    # ------------------------------------------------------------------

    def _payload(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "body": self.message,
            "data": {
                "type": (self.notification_category or "General").lower(),
                "category": self.notification_category,
                "notification_id": self.name,
                "timestamp": get_datetime().isoformat(),
                "screen": self.get_target_screen(),
            },
            "sound": "default",
        }

    def get_target_screen(self) -> str:
        """Determine the target screen based on notification category."""
        screen_map = {
            "Academic": "grades",
            "Announcements": "announcements",
            "Fees": "fees",
            "Events": "schedule",
            "Examinations": "grades",
        }
        return screen_map.get(self.notification_category, "notifications")

    def _alert_phones(self, entries: List[Dict[str, Any]]):
        """Push to every phone signed in to each recipient's account."""
        entries = [e for e in entries if e.get("user")]
        if not entries:
            return

        tokens_by_user = get_active_push_tokens(list({e["user"] for e in entries}))
        payload = self._payload()
        names = {
            r.name: r.student_name
            for r in frappe.get_all(
                "Student", filters={"name": ("in", [e["student"] for e in entries])}, fields=["name", "student_name"]
            )
        }

        messages, owners = [], []
        for e in entries:
            e["tickets"], e["errors"] = [], []
            tokens = tokens_by_user.get(e["user"]) or []
            e["devices"] = len(tokens)
            for token in tokens:
                message = dict(payload)
                message["to"] = token
                # Tells the app which child this is for, so on a phone signed
                # in to several children it can open the right account.
                message["data"] = dict(
                    payload["data"],
                    student_id=e["student"],
                    student_name=names.get(e["student"]),
                    user_id=e["user"],
                    inbox_id=e["name"],
                )
                messages.append(message)
                owners.append((e, token))

        for start in range(0, len(messages), EXPO_SEND_BATCH):
            batch = messages[start:start + EXPO_SEND_BATCH]
            batch_owners = owners[start:start + EXPO_SEND_BATCH]
            tickets, error = send_to_expo(batch)
            for i, (e, token) in enumerate(batch_owners):
                ticket = tickets[i] if tickets else {"status": "error", "message": error}
                if ticket.get("status") == "ok":
                    e["tickets"].append({"id": ticket.get("id"), "token": token})
                else:
                    details = ticket.get("details") or {}
                    reason = details.get("error") or ticket.get("message") or "Unknown error"
                    e["errors"].append(reason)
                    if reason == "DeviceNotRegistered":
                        deactivate_token(token)

        for e in entries:
            if not e["devices"]:
                status, reason = "No Device", "No phone is signed in to this student's account"
            elif e["tickets"]:
                status, reason = "Sent", None
            else:
                status, reason = "Failed", (e["errors"][0] if e["errors"] else "Unknown error")[:140]
            frappe.db.set_value(
                "Student Notification",
                e["name"],
                {
                    "push_status": status,
                    "push_devices": e["devices"],
                    "push_error": reason,
                    "push_tickets": json.dumps(e["tickets"]) if e["tickets"] else None,
                },
                update_modified=False,
            )


def send_to_expo(messages):
    """POST a batch to Expo. Returns (tickets, None) or (None, error message)."""
    try:
        response = requests.post(
            EXPO_SEND_URL,
            headers={
                "Accept": "application/json",
                "Accept-encoding": "gzip, deflate",
                "Content-Type": "application/json",
            },
            json=messages,
            timeout=30,
        )
        body = response.json() if response.content else {}
    except Exception as e:
        return None, f"Could not reach push service: {e}"[:140]

    tickets = body.get("data") if isinstance(body, dict) else None
    if not isinstance(tickets, list) or len(tickets) != len(messages):
        errors = body.get("errors") if isinstance(body, dict) else body
        return None, f"Push service rejected the request: {json.dumps(errors)}"[:140]
    return tickets, None


def deactivate_token(token):
    """The app was uninstalled or its token rotated; stop sending to it."""
    frappe.db.set_value("Push Token", {"push_token": token}, "is_active", 0)


def get_active_push_tokens(users: List[str]) -> Dict[str, List[str]]:
    """Active push tokens per user.

    A phone signed in to several accounts (a parent with a login per child) is
    registered under each of them, so it gets every one of those accounts'
    notifications. That is intended.
    """
    if not users:
        return {}
    rows = frappe.get_all(
        "Push Token",
        filters={"user": ("in", users), "is_active": 1},
        fields=["push_token", "user"],
    )
    result: Dict[str, List[str]] = {}
    for row in rows:
        tokens = result.setdefault(row.user, [])
        if row.push_token not in tokens:
            tokens.append(row.push_token)
    return result


def update_delivery_summary(name: str) -> Dict[str, Any]:
    """Recount a notification's inbox entries and set its status and summary."""
    counts = dict(
        frappe.db.sql(
            """select push_status, count(*) from `tabStudent Notification`
            where notification = %s group by push_status""",
            name,
        )
    )
    total = sum(counts.values())
    read = frappe.db.count("Student Notification", {"notification": name, "is_read": 1})
    alerted = counts.get("Sent", 0) + counts.get("Delivered", 0)
    failed = counts.get("Failed", 0)
    no_device = counts.get("No Device", 0) + counts.get("No Account", 0)

    if not total:
        status = "Failed"
        summary = "No students matched the selected recipients."
    else:
        status = "Partially Sent" if failed else "Sent"
        summary = (
            f"In the app inbox of {total} student(s). "
            f"Phone alert reached {alerted}; {failed} failed; {no_device} have no phone signed in. "
            f"Read by {read}."
        )

    values = {
        "status": status,
        "recipient_count": total,
        "sent_count": alerted,
        "failed_count": failed,
        "no_device_count": no_device,
        "read_count": read,
        "delivery_summary": summary,
    }
    if total and not frappe.db.get_value("App Notification", name, "sent_date"):
        values["sent_date"] = now()
    frappe.db.set_value("App Notification", name, values, update_modified=False)
    return values


# ----------------------------------------------------------------------
# receipts
# ----------------------------------------------------------------------

def check_receipts(name: str = None):
    """Ask Expo whether alerts it accepted actually reached the phones.

    Expo keeps receipts for about a day, so only recent alerts are checked.
    """
    filters = {
        "push_status": "Sent",
        "push_tickets": ("is", "set"),
        "sent_on": (">", add_to_date(now_datetime(), days=-1)),
    }
    if name:
        filters["notification"] = name
    rows = frappe.get_all(
        "Student Notification",
        filters=filters,
        fields=["name", "notification", "push_tickets"],
        limit_page_length=0,
    )
    if not rows:
        return 0

    ids = []
    for r in rows:
        r.tickets = json.loads(r.push_tickets or "[]")
        ids.extend(t["id"] for t in r.tickets if t.get("id"))

    receipts: Dict[str, Any] = {}
    for start in range(0, len(ids), EXPO_RECEIPT_BATCH):
        try:
            response = requests.post(
                EXPO_RECEIPTS_URL,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json={"ids": ids[start:start + EXPO_RECEIPT_BATCH]},
                timeout=30,
            )
            receipts.update((response.json() or {}).get("data") or {})
        except Exception:
            frappe.log_error(frappe.get_traceback(), "App Notification receipt check failed")

    touched = set()
    for r in rows:
        ready = [t for t in r.tickets if t.get("id") in receipts]
        if not ready:
            continue  # not ready yet
        ok, errors = False, []
        for t in ready:
            receipt = receipts[t["id"]]
            if receipt.get("status") == "ok":
                ok = True
                continue
            reason = (receipt.get("details") or {}).get("error") or receipt.get("message") or "Unknown error"
            errors.append(reason)
            if reason == "DeviceNotRegistered" and t.get("token"):
                deactivate_token(t["token"])
        if ok:
            values = {"push_status": "Delivered", "push_error": None}
        elif len(ready) == len(r.tickets):
            values = {"push_status": "Failed", "push_error": errors[0][:140]}
        else:
            continue
        frappe.db.set_value("Student Notification", r.name, values, update_modified=False)
        touched.add(r.notification)

    for parent in touched:
        update_delivery_summary(parent)
    return len(touched)


def check_recent_receipts():
    """Scheduler entry point."""
    check_receipts()


# ----------------------------------------------------------------------
# permissions: students only see what was addressed to them
# ----------------------------------------------------------------------

def get_permission_query_conditions(user=None):
    from education.education.student_scope import student_for_user

    student = student_for_user(user or frappe.session.user)
    if not student:
        return ""
    s = frappe.db.escape(student)
    return f"""(`tabApp Notification`.docstatus = 1 and (
        (`tabApp Notification`.send_to_all_students = 1
            and not exists (select 1 from `tabApp Notification Student` ans where ans.parent = `tabApp Notification`.name)
            and not exists (select 1 from `tabApp Notification Student Group` ansg where ansg.parent = `tabApp Notification`.name))
        or exists (select 1 from `tabApp Notification Student` ans
            where ans.parent = `tabApp Notification`.name and ans.student = {s})
        or exists (select 1 from `tabApp Notification Student Group` ansg
            inner join `tabStudent Group Student` sgs on sgs.parent = ansg.student_group
            where ansg.parent = `tabApp Notification`.name and sgs.student = {s} and sgs.active = 1)
    ))"""


def has_permission(doc, ptype=None, user=None):
    from education.education.student_scope import student_for_user

    student = student_for_user(user or frappe.session.user)
    if not student:
        return True
    if doc.docstatus != 1:
        return False
    return is_addressed_to(doc, student)


def is_addressed_to(doc, student) -> bool:
    students = [r.student for r in doc.get("students") or []]
    groups = [r.student_group for r in doc.get("student_groups") or []]
    if doc.send_to_all_students and not students and not groups:
        return True
    if student in students:
        return True
    if groups:
        return bool(frappe.db.exists(
            "Student Group Student",
            {"parent": ("in", groups), "student": student, "active": 1},
        ))
    return False


# ----------------------------------------------------------------------
# whitelisted
# ----------------------------------------------------------------------

@frappe.whitelist()
def send_test_notification(notification_name):
    """Send a submitted notification that never went out (e.g. it errored)."""
    doc = frappe.get_doc("App Notification", notification_name)
    doc.check_permission("submit")

    if doc.status in ("Sent", "Partially Sent"):
        frappe.throw("This notification has already been sent")

    doc.send_push_notifications()
    return {"status": doc.status, "message": doc.delivery_summary}


@frappe.whitelist()
def resend_failed(notification_name):
    """Retry the phone alerts that failed, without re-alerting anyone who got it."""
    doc = frappe.get_doc("App Notification", notification_name)
    doc.check_permission("submit")
    if doc.docstatus != 1:
        frappe.throw("Submit the notification first")
    doc.send_push_notifications(only_failed=True)
    return {"status": doc.status, "message": doc.delivery_summary}


@frappe.whitelist()
def refresh_delivery_status(notification_name):
    """Pull delivery receipts from Expo for this notification now."""
    doc = frappe.get_doc("App Notification", notification_name)
    doc.check_permission("read")
    check_receipts(notification_name)
    values = update_delivery_summary(notification_name)
    return {"status": values["status"], "message": values["delivery_summary"]}


@frappe.whitelist()
def get_recipient_preview(student_groups=None, students=None, send_to_all_students=0):
    """How many students a notification would reach, and how many have a phone signed in."""
    frappe.has_permission("App Notification", "create", throw=True)
    if isinstance(student_groups, str):
        student_groups = json.loads(student_groups or "[]")
    if isinstance(students, str):
        students = json.loads(students or "[]")

    doc = frappe.new_doc("App Notification")
    doc.send_to_all_students = cint(send_to_all_students)
    for g in student_groups or []:
        doc.append("student_groups", {"student_group": g})
    for s in students or []:
        doc.append("students", {"student": s})
    if doc.students or doc.student_groups:
        doc.send_to_all_students = 0

    recipients = doc.get_recipient_students()
    users = frappe.get_all(
        "Student",
        filters={"name": ("in", recipients or [""]), "enabled": 1, "user": ("is", "set")},
        pluck="user",
    )
    with_device = len(get_active_push_tokens(users))
    return {"students": len(recipients), "with_device": with_device}


@frappe.whitelist()
def get_student_count_for_groups(student_groups):
    """Get total student count for selected student groups"""
    if isinstance(student_groups, str):
        student_groups = json.loads(student_groups)

    unique_students = set()

    for group_name in student_groups:
        if group_name:
            students = frappe.get_all(
                "Student Group Student",
                filters={"parent": group_name, "active": 1},
                pluck="student"
            )
            unique_students.update(students)

    return len(unique_students)


@frappe.whitelist()
def get_all_students_count():
    """Get count of all active students"""
    return frappe.db.count("Student", filters={"enabled": 1})
