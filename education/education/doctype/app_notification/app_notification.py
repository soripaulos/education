# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from typing import Any, Dict, List

import frappe
import requests
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime, now, now_datetime

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
        """Send push notifications when the document is submitted."""
        self.send_push_notifications()

    def send_push_notifications(self, only_failed=False):
        """Send push notifications to the selected recipients and record what happened to each.

        Never raises: a failed push must not roll back the document that
        triggered it (a teacher's parent message, an incident report, ...).
        The outcome is recorded on the document's delivery report instead.
        """
        try:
            if only_failed:
                deliveries = self._failed_deliveries_for_retry()
            else:
                deliveries = self._build_deliveries()
                self._replace_delivery_rows(deliveries)

            to_send = [d for d in deliveries if d["push_token"] and d["status"] in ("Pending", "Failed")]
            if to_send:
                self._send_via_expo(to_send)
                for d in to_send:
                    self._save_delivery_row(d)

            self._update_summary()

            if self.status == "Failed" and not self.sent_count:
                frappe.msgprint(
                    "The notification could not be delivered to any device. "
                    "See the Delivery Report section for the reason per student."
                )
            else:
                frappe.msgprint(
                    f"Push notification sent to {self.sent_count} device(s) "
                    f"for {self.recipient_count} student(s)."
                )
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

    def _build_deliveries(self) -> List[Dict[str, Any]]:
        """One entry per (student, device) that should receive this notification,
        plus one entry for each student that cannot be reached at all."""
        students = self.get_recipient_students()
        if not students:
            return []

        student_rows = frappe.get_all(
            "Student",
            filters={"name": ("in", students)},
            fields=["name", "student_name", "user", "enabled"],
        )
        by_student = {s.name: s for s in student_rows}
        user_to_students: Dict[str, List[str]] = {}
        for s in student_rows:
            if s.enabled and s.user:
                user_to_students.setdefault(s.user, []).append(s.name)

        tokens_by_user = get_active_push_tokens(list(user_to_students))

        deliveries = []
        for student in students:
            s = by_student.get(student)
            base = {
                "student": student,
                "student_name": s.student_name if s else None,
                "user": s.user if s else None,
                "push_token": None,
                "ticket_id": None,
                "error": None,
            }
            if not s or not s.enabled:
                deliveries.append({**base, "status": "No Account", "error": "Student is disabled or missing"})
                continue
            if not s.user:
                deliveries.append({**base, "status": "No Account", "error": "Student has no app login"})
                continue

            tokens = tokens_by_user.get(s.user) or []
            if not tokens:
                deliveries.append({
                    **base,
                    "status": "No Device",
                    "error": "No phone is currently signed in to this student's account",
                })
                continue
            for token in tokens:
                deliveries.append({**base, "push_token": token, "status": "Pending"})

        return deliveries

    # ------------------------------------------------------------------
    # sending
    # ------------------------------------------------------------------

    def _prepare_notification_data(self) -> Dict[str, Any]:
        """Prepare the payload for the push notification."""
        return {
            "title": self.title,
            "body": self.message,
            "data": {
                "type": (self.notification_category or "General").lower(),
                "category": self.notification_category,
                "notification_id": self.name,
                "timestamp": get_datetime().isoformat(),
                "screen": self.get_target_screen()
            },
            "sound": "default"
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

    def _send_via_expo(self, deliveries: List[Dict[str, Any]]):
        """Send to each delivery's device and store Expo's per-message ticket on it."""
        payload = self._prepare_notification_data()
        for start in range(0, len(deliveries), EXPO_SEND_BATCH):
            batch = deliveries[start:start + EXPO_SEND_BATCH]
            messages = []
            for d in batch:
                message = dict(payload)
                message["to"] = d["push_token"]
                # Lets the app double-check the push is for the account signed in.
                message["data"] = dict(payload["data"], user=d["user"], student=d["student"])
                messages.append(message)

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
                for d in batch:
                    d["status"] = "Failed"
                    d["error"] = f"Could not reach push service: {e}"[:140]
                continue

            tickets = body.get("data") if isinstance(body, dict) else None
            if not isinstance(tickets, list) or len(tickets) != len(batch):
                error = json.dumps(body.get("errors") if isinstance(body, dict) else body)[:140]
                for d in batch:
                    d["status"] = "Failed"
                    d["error"] = f"Push service rejected the request: {error}"
                continue

            for d, ticket in zip(batch, tickets):
                apply_ticket(d, ticket)

    # ------------------------------------------------------------------
    # delivery report
    # ------------------------------------------------------------------

    def _replace_delivery_rows(self, deliveries: List[Dict[str, Any]]):
        """Store one App Notification Delivery record per entry.

        Kept as a separate, staff-only doctype rather than a child table so a
        student who can read a broadcast never sees other students' devices.
        """
        frappe.db.delete("App Notification Delivery", {"notification": self.name})
        if not deliveries:
            return
        stamp = now()
        user = frappe.session.user
        fields = [
            "name", "creation", "modified", "owner", "modified_by", "docstatus",
            "notification", "student", "student_name", "user", "push_token",
            "status", "ticket_id", "error", "updated_on",
        ]
        values = []
        for d in deliveries:
            d["row_name"] = frappe.generate_hash(length=12)
            values.append((
                d["row_name"], stamp, stamp, user, user, 0,
                self.name, d["student"], d.get("student_name"), d.get("user"), d.get("push_token"),
                d["status"], d.get("ticket_id"), d.get("error"), stamp,
            ))
        frappe.db.bulk_insert("App Notification Delivery", fields=fields, values=values)

    def _failed_deliveries_for_retry(self) -> List[Dict[str, Any]]:
        """Failed rows whose device is still registered to the student's account."""
        rows = frappe.get_all(
            "App Notification Delivery",
            filters={"notification": self.name, "status": "Failed", "push_token": ("is", "set"), "user": ("is", "set")},
            fields=["name", "student", "user", "push_token"],
        )
        active = get_active_push_tokens(list({r.user for r in rows}))
        retry = []
        for r in rows:
            if r.push_token not in (active.get(r.user) or []):
                frappe.db.set_value(
                    "App Notification Delivery",
                    r.name,
                    {"status": "No Device", "error": "Device is no longer registered to this account", "updated_on": now()},
                )
                continue
            retry.append({
                "row_name": r.name,
                "student": r.student,
                "user": r.user,
                "push_token": r.push_token,
                "status": "Failed",
                "ticket_id": None,
                "error": None,
            })
        return retry

    def _save_delivery_row(self, d: Dict[str, Any]):
        if d.get("row_name"):
            frappe.db.set_value(
                "App Notification Delivery",
                d["row_name"],
                {"status": d["status"], "ticket_id": d["ticket_id"], "error": d["error"], "updated_on": now()},
            )

    def _update_summary(self):
        # Copy the stored values onto this instance rather than reloading it,
        # which is unsafe while the document is still being submitted.
        self.update(update_delivery_summary(self.name))


def apply_ticket(d: Dict[str, Any], ticket: Dict[str, Any]):
    """Record one Expo push ticket on a delivery entry."""
    if ticket.get("status") == "ok":
        d["status"] = "Sent"
        d["ticket_id"] = ticket.get("id")
        d["error"] = None
        return
    details = ticket.get("details") or {}
    d["status"] = "Failed"
    d["error"] = (details.get("error") or ticket.get("message") or "Unknown error")[:140]
    if details.get("error") == "DeviceNotRegistered":
        # The app was uninstalled or the token rotated; stop sending to it.
        frappe.db.set_value("Push Token", {"push_token": d["push_token"]}, "is_active", 0)


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


def update_delivery_summary(name: str):
    """Recount the delivery rows of a notification and set its status."""
    rows = frappe.get_all(
        "App Notification Delivery",
        filters={"notification": name},
        fields=["student", "status"],
        limit_page_length=0,
    )
    students = {r.student for r in rows}
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r.status] = counts.get(r.status, 0) + 1

    sent = counts.get("Sent", 0) + counts.get("Delivered", 0)
    failed = counts.get("Failed", 0)
    unreachable = len({r.student for r in rows if r.status in ("No Device", "No Account")})
    reached = len({r.student for r in rows if r.status in ("Sent", "Delivered")})

    if sent and not failed:
        status = "Sent"
    elif sent:
        status = "Partially Sent"
    else:
        status = "Failed"

    summary = (
        f"{reached} of {len(students)} student(s) reached on {sent} device(s). "
        f"{failed} device(s) failed, {unreachable} student(s) have no signed-in device."
    )

    values = {
        "status": status,
        "recipient_count": len(students),
        "sent_count": sent,
        "failed_count": failed,
        "no_device_count": unreachable,
        "delivery_summary": summary,
    }
    if sent and not frappe.db.get_value("App Notification", name, "sent_date"):
        values["sent_date"] = now()
    frappe.db.set_value("App Notification", name, values, update_modified=False)
    return values


# ----------------------------------------------------------------------
# receipts
# ----------------------------------------------------------------------

def check_receipts(name: str = None):
    """Ask Expo whether pushes that were accepted actually reached the phone.

    Expo keeps receipts for about a day, so only recent tickets are checked.
    """
    filters = {
        "status": "Sent",
        "ticket_id": ("is", "set"),
        "updated_on": (">", add_to_date(now_datetime(), days=-1)),
    }
    if name:
        filters["notification"] = name
    rows = frappe.get_all(
        "App Notification Delivery",
        filters=filters,
        fields=["name", "notification", "ticket_id", "push_token"],
        limit_page_length=5000,
    )
    if not rows:
        return 0

    touched = set()
    for start in range(0, len(rows), EXPO_RECEIPT_BATCH):
        batch = rows[start:start + EXPO_RECEIPT_BATCH]
        try:
            response = requests.post(
                EXPO_RECEIPTS_URL,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json={"ids": [r.ticket_id for r in batch]},
                timeout=30,
            )
            receipts = (response.json() or {}).get("data") or {}
        except Exception:
            frappe.log_error(frappe.get_traceback(), "App Notification receipt check failed")
            continue

        for r in batch:
            receipt = receipts.get(r.ticket_id)
            if not receipt:
                continue  # not ready yet
            if receipt.get("status") == "ok":
                values = {"status": "Delivered", "error": None}
            else:
                details = receipt.get("details") or {}
                error = details.get("error") or receipt.get("message") or "Unknown error"
                values = {"status": "Failed", "error": error[:140]}
                if error == "DeviceNotRegistered" and r.push_token:
                    frappe.db.set_value("Push Token", {"push_token": r.push_token}, "is_active", 0)
            values["updated_on"] = now()
            frappe.db.set_value("App Notification Delivery", r.name, values)
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
    """API method to send a test notification"""
    doc = frappe.get_doc("App Notification", notification_name)
    doc.check_permission("submit")

    if doc.status in ("Sent", "Partially Sent"):
        frappe.throw("This notification has already been sent")

    doc.send_push_notifications()
    return {"status": "success", "message": doc.delivery_summary}


@frappe.whitelist()
def resend_failed(notification_name):
    """Retry the devices that failed, without re-notifying anyone who already got it."""
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
    doc.reload()
    return {"status": doc.status, "message": doc.delivery_summary}


@frappe.whitelist()
def get_recipient_preview(student_groups=None, students=None, send_to_all_students=0):
    """How many students a notification would reach, and how many have a device."""
    frappe.has_permission("App Notification", "create", throw=True)
    if isinstance(student_groups, str):
        student_groups = json.loads(student_groups or "[]")
    if isinstance(students, str):
        students = json.loads(students or "[]")

    doc = frappe.new_doc("App Notification")
    doc.send_to_all_students = frappe.utils.cint(send_to_all_students)
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
