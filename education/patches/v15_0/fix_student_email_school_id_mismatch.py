"""Repair students whose `student_email_id` encodes someone else's school ID.

Background
----------
The registration pages derive a student's school email from the school ID by
stripping the slashes: ``M1/46478/18`` -> ``m14647818@m.b.s``. When a student
who already attended the school was registered through the *New* path, a fresh
``/18`` school ID was generated and that derived email (and the User created
from it) was stored on the record. Correcting ``custom_school_id`` afterwards
left ``student_email_id`` - and often the linked ``user`` - pointing at the
discarded ID, so the student showed up under a username that was not theirs.

The canonical form is the school ID with the domain appended verbatim:

    M1/6134/14  ->  M1/6134/14@m.b.s

This patch only touches records whose email matches *neither* accepted spelling
of their own school ID (with or without slashes); records that merely use the
slash-less spelling of their own ID are left alone, as are external addresses
such as personal Gmail accounts.

User records are reconciled as follows:
  * the canonical User already exists -> the Student is linked to it and the
    now-unreferenced duplicate is removed (or disabled if it cannot be deleted);
  * no canonical User exists -> the stale one is renamed to the canonical name,
    which preserves its roles, links and login history.
"""

import frappe

DOMAIN = "@m.b.s"

# Applicant rows are corrected for the intake currently being registered only;
# see fix_applicants().
CURRENT_ACADEMIC_YEAR = "2019 E.C."


def canonical_email(school_id):
	return f"{(school_id or '').strip()}{DOMAIN}"


def own_spellings(school_id):
	"""The addresses that legitimately belong to this school ID."""
	school_id = (school_id or "").strip()
	return {
		f"{school_id}{DOMAIN}".lower(),
		f"{school_id.replace('/', '')}{DOMAIN}".lower(),
	}


def execute():
	users = {
		name.lower(): name for (name,) in frappe.db.sql("SELECT name FROM `tabUser`")
	}
	repaired = fix_students(users)
	fix_applicants()
	frappe.db.commit()
	frappe.log_error(
		message=f"Repaired {repaired} Student record(s) with a mismatched school email.",
		title="fix_student_email_school_id_mismatch",
	)


def fix_students(users):
	students = frappe.db.sql(
		"""
		SELECT name, custom_school_id, student_email_id, user
		FROM `tabStudent`
		WHERE student_email_id LIKE %s
		""",
		(f"%{DOMAIN}",),
		as_dict=True,
	)

	# Which Students point at a given User, so a duplicate is only dropped once
	# nothing references it any more.
	referenced_by = {}
	for row in students:
		if row.user:
			referenced_by.setdefault(row.user.lower(), set()).add(row.name)

	repaired = 0
	for row in students:
		school_id = (row.custom_school_id or "").strip()
		if not school_id:
			continue
		if (row.student_email_id or "").lower() in own_spellings(school_id):
			continue

		target = canonical_email(school_id)
		current_user = (row.user or "").strip()
		updates = {"student_email_id": target}

		if current_user.lower() == target.lower():
			# The login is already right; only the email field drifted.
			pass
		elif target.lower() in users:
			# Reuse the account that already carries the correct school ID and
			# retire the duplicate this record was pointing at.
			updates["user"] = users[target.lower()]
			if current_user:
				referenced_by.get(current_user.lower(), set()).discard(row.name)
				if not referenced_by.get(current_user.lower()):
					retire_duplicate_user(current_user)
		elif current_user and current_user.lower() in users:
			# Nothing to merge into: rename the stale account into shape so its
			# roles and history follow the student.
			rename_user(users[current_user.lower()], target, users)
			updates["user"] = target
		else:
			updates["user"] = create_user(row, target)
			users[target.lower()] = target

		# Written straight to the table: this is a surgical correction and must
		# not re-run Student.validate(), which would try to mint users again.
		frappe.db.set_value("Student", row.name, updates, update_modified=False)
		repaired += 1

	return repaired


def fix_applicants():
	"""Re-point Student Applicant rows at their own school ID.

	Scoped to existing students re-applying for the current intake, whose email
	was copied off the Student record wholesale. Earlier academic years are
	left as filed: those applications are closed history, and rewriting them
	would edit the record of what was actually submitted at the time.
	"""
	applicants = frappe.db.sql(
		"""
		SELECT name, custom_school_id, student_email_id
		FROM `tabStudent Applicant`
		WHERE applicant_type = 'Existing'
		  AND academic_year = %s
		  AND student_email_id LIKE %s
		""",
		(CURRENT_ACADEMIC_YEAR, f"%{DOMAIN}"),
		as_dict=True,
	)

	for row in applicants:
		school_id = (row.custom_school_id or "").strip()
		if not school_id:
			continue
		if (row.student_email_id or "").lower() in own_spellings(school_id):
			continue
		frappe.db.set_value(
			"Student Applicant",
			row.name,
			{"student_email_id": canonical_email(school_id)},
			update_modified=False,
		)


def rename_user(current, target, users):
	try:
		frappe.rename_doc("User", current, target, force=True, ignore_permissions=True)
		frappe.db.set_value("User", target, "email", target, update_modified=False)
		users.pop(current.lower(), None)
		users[target.lower()] = target
	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title=f"Could not rename User {current} -> {target}",
		)


def create_user(student, target):
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": target,
			"first_name": student.get("first_name") or target,
			"send_welcome_email": 0,
			"user_type": "Website User",
		}
	)
	user.flags.ignore_permissions = True
	user.insert(ignore_permissions=True)
	user.add_roles("Student")
	return user.name


def retire_duplicate_user(name):
	"""Drop a student account nothing points at any more.

	Deletion is attempted first so the address is free for reuse; accounts that
	are still referenced elsewhere (comments, versions, logins) are disabled
	instead, which is enough to stop them being handed out again.
	"""
	if frappe.db.get_value("User", name, "last_login"):
		# Somebody has actually signed in with this account - keep it, just
		# take it out of circulation rather than destroying the audit trail.
		frappe.db.set_value("User", name, "enabled", 0, update_modified=False)
		return

	try:
		# No `force`: if anything still links to the account the delete fails
		# and it is disabled instead, rather than leaving dangling references.
		frappe.delete_doc("User", name, ignore_permissions=True)
	except Exception:
		frappe.db.set_value("User", name, "enabled", 0, update_modified=False)
		frappe.log_error(
			message=frappe.get_traceback(),
			title=f"Could not delete duplicate User {name}; disabled instead",
		)
