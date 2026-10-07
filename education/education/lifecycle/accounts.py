"""Student logins, created on their own schedule rather than during enrollment.

Frappe refuses to create more than ``throttle_user_limit`` (default 60)
Users in an hour. Minting logins inside enrollment therefore stalled every
large intake. Enrollment now never creates a login. This module does it
afterwards, in bulk, with the throttle lifted for the duration of the job
only.

Login: the canonical school address for the School ID (``M1/1234/18@m.b.s``),
or the family's own address where one was recorded.

Initial password: the family phone number written locally
(``0912345678``); if the password policy rejects that, ``251912345678``.
No welcome email is sent - the school domain does not receive mail.
"""

from contextlib import contextmanager

import frappe
from frappe import _

from education.education.lifecycle.common import local_phone_digits, phone_password_candidates

STUDENT_ROLE = "Student"


@contextmanager
def unthrottled_user_creation():
	"""Lift Frappe's hourly cap on new Users for this process only.

	``throttle_user_creation`` reads ``frappe.local.conf``; a private copy is
	swapped in and the original restored afterwards, so nothing else about
	the site configuration (or any other worker) is affected.
	"""
	original = frappe.local.conf
	frappe.local.conf = frappe._dict(original)
	frappe.local.conf.throttle_user_limit = 10**9
	try:
		yield
	finally:
		frappe.local.conf = original


def student_login(student):
	"""The login a Student should have, from their School ID."""
	from education.education.api import _resolve_student_email

	return _resolve_student_email(student.custom_school_id, student.student_email_id)


def student_phone(student):
	"""The phone number a student's password is built from.

	The student's own mobile field is what registration fills with the
	family's primary number. A guardian's number is the fallback.
	"""
	if local_phone_digits(student.get("student_mobile_number")):
		return student.get("student_mobile_number")
	guardians = [row.guardian for row in student.get("guardians") or [] if row.guardian]
	for guardian in guardians:
		for fieldname in ("mobile_number", "alternate_number"):
			if not frappe.get_meta("Guardian").has_field(fieldname):
				continue
			number = frappe.db.get_value("Guardian", guardian, fieldname)
			if local_phone_digits(number):
				return number
	return ""


def choose_password(phone, user_data):
	"""First phone-based password the site's password policy accepts.

	Returns ``(password, rule)`` where rule is "0-prefix" or "251-prefix",
	or ``(None, reason)`` when no candidate exists or none is accepted.
	"""
	from frappe.core.doctype.user.user import test_password_strength

	candidates = phone_password_candidates(phone)
	if not candidates:
		return None, _("No usable phone number")
	for password, rule in zip(candidates, ("0-prefix", "251-prefix")):
		result = test_password_strength(password, user_data=user_data) or {}
		feedback = result.get("feedback") or {}
		# An empty result means the password policy is switched off.
		if not result or feedback.get("password_policy_validation_passed"):
			return password, rule
	return None, _("Phone-based passwords rejected by the password policy")


def user_has_password(user):
	return bool(
		frappe.db.sql(
			"""SELECT 1 FROM `__Auth` WHERE doctype='User' AND name=%s AND fieldname='password'""",
			(user,),
		)
	)


def _set_password(user, password):
	from frappe.utils.password import update_password

	update_password(user, password, logout_all_sessions=False)


def ensure_student_user(student, set_password=True, overwrite_password=False):
	"""Make sure ``student`` has a working login. Safe to run repeatedly.

	* An existing account at the student's address is linked, not duplicated.
	* A new account is created as a Website User with the Student role.
	* The phone-based password is set on new accounts, on existing ones that
	  have never had a password, and on any account when
	  ``overwrite_password`` is set.

	Returns a dict: status ("Created", "Linked", "Already Set Up", "Failed"),
	user, password (only when one was set in this call), password_rule, message.
	"""
	if isinstance(student, str):
		student = frappe.get_doc("Student", student)

	result = frappe._dict(
		student=student.name, user="", status="", password="", password_rule="", message=""
	)
	login = student_login(student)
	if not login:
		result.status = "Failed"
		result.message = _("Student has no School ID or email to build a login from")
		return result
	result.user = login

	updates = {}
	if student.student_email_id != login:
		updates["student_email_id"] = login

	existing = frappe.db.exists("User", login)
	if existing:
		result.status = "Linked" if student.user != existing else "Already Set Up"
		login = existing
		if not frappe.db.get_value("User", login, "enabled") and student.enabled:
			frappe.db.set_value("User", login, "enabled", 1)
			result.message = _("Login was disabled and has been re-enabled")
	else:
		login = create_user(student, login)
		result.status = "Created"

	if student.user != login:
		updates["user"] = login
	if updates:
		frappe.db.set_value("Student", student.name, updates)

	wants_password = set_password and (
		result.status == "Created" or overwrite_password or not user_has_password(login)
	)
	if wants_password:
		password, rule = set_phone_password(student, login)
		result.password_rule = rule
		if password:
			result.password = password
		else:
			result.message = (result.message + " " if result.message else "") + _(
				"Password not set: {0}"
			).format(rule)
	return result


def create_user(student, login):
	"""Create the Website User for a student. Returns the User's name."""
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": login,
			"first_name": student.first_name or login,
			"middle_name": student.middle_name,
			"last_name": student.last_name,
			"gender": student.gender,
			"user_type": "Website User",
			"send_welcome_email": 0,
			"enabled": 1 if student.enabled else 0,
			"roles": [{"role": STUDENT_ROLE}],
		}
	)
	user.flags.ignore_permissions = True
	user.flags.no_welcome_mail = True
	user.insert(ignore_permissions=True)
	return user.name


def set_phone_password(student, login):
	"""Set the phone-based initial password. Returns (password or None, rule/reason)."""
	user_data = (student.first_name, student.middle_name, student.last_name, login, None)
	password, rule = choose_password(student_phone(student), user_data)
	if password:
		_set_password(login, password)
	return password, rule
