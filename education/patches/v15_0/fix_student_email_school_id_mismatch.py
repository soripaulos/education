"""Bring student school addresses and logins onto their own school ID.

Background
----------
The registration pages used to derive a student's school address by stripping
the slashes out of the school ID: ``M1/57126/18`` -> ``m15712618@m.b.s``. Two
problems came out of that.

1. A returning student registered through the *New* path was issued a fresh
   ``/18`` school ID, and the address (plus the User minted from it) stuck to
   the record even after ``custom_school_id`` was corrected back to the real
   ID. The student then appeared under a username belonging to an ID nobody
   holds, and every later application copied that stale address forward.

2. Even where the address did encode the student's own ID, the slash-less
   spelling left the record disagreeing with the ``M1/57126/18@m.b.s`` form
   used everywhere else.

The canonical form is the school ID with the domain appended verbatim::

    M1/57126/18  ->  M1/57126/18@m.b.s

Accounts are reconciled conservatively:
  * the canonical User already exists -> the Student is linked to it and the
    superseded account is removed once nothing references it;
  * no canonical User exists and the current one has never been signed into ->
    it is renamed, which carries its roles and links across;
  * no canonical User exists but the current one is **in active use** -> the
    record is left alone and reported, because renaming it would change a
    login somebody is relying on.

Addresses supplied by the family (anything outside ``@m.b.s``) are never
rewritten.
"""

import frappe

DOMAIN = "@m.b.s"

# Applicant rows are corrected for the intake currently being registered only;
# see fix_applicants().
CURRENT_ACADEMIC_YEAR = "2019 E.C."


def canonical_email(school_id):
	return f"{(school_id or '').strip()}{DOMAIN}"


def own_spellings(school_id):
	"""Addresses that encode this school ID, in either spelling."""
	school_id = (school_id or "").strip()
	return {
		f"{school_id}{DOMAIN}".lower(),
		f"{school_id.replace('/', '')}{DOMAIN}".lower(),
	}


def is_ours(address):
	"""True for a school-issued address, false for a family mailbox."""
	return (address or "").strip().lower().endswith(DOMAIN)


def execute():
	users = {name.lower(): name for (name,) in frappe.db.sql("SELECT name FROM `tabUser`")}
	stats = fix_students(users)
	stats["applicants"] = fix_applicants()
	frappe.db.commit()

	summary = ", ".join(f"{key}={value}" for key, value in sorted(stats.items()))
	frappe.log_error(
		message=f"Student school-address repair complete: {summary}",
		title="fix_student_email_school_id_mismatch",
	)


def fix_students(users):
	students = frappe.db.sql(
		"""
		SELECT name, custom_school_id, student_email_id, user, first_name
		FROM `tabStudent`
		WHERE custom_school_id IS NOT NULL AND custom_school_id != ''
		""",
		as_dict=True,
	)

	# Which Students point at a given User, so an account is only retired once
	# nothing references it any more.
	referenced_by = {}
	for row in students:
		if row.user:
			referenced_by.setdefault(row.user.lower(), set()).add(row.name)

	stats = {"email_only": 0, "relinked": 0, "renamed": 0, "created": 0, "skipped_in_use": 0}
	skipped = []

	for row in students:
		school_id = (row.custom_school_id or "").strip()
		target = canonical_email(school_id)
		email = (row.student_email_id or "").strip()
		user = (row.user or "").strip()

		# A school address that does not encode this student's ID, or a login
		# that is not the canonical spelling of it, is what needs correcting.
		email_wrong = is_ours(email) and email.lower() not in own_spellings(school_id)
		user_wrong = is_ours(user) and user.lower() != target.lower()
		if not (email_wrong or user_wrong):
			continue

		updates = {}
		if is_ours(email) or not email:
			updates["student_email_id"] = target

		superseded = None
		if user.lower() == target.lower():
			stats["email_only"] += 1
		elif target.lower() in users:
			# Reuse the account already carrying the correct school ID and
			# retire the one this record was pointing at. The retirement is
			# deferred until after the Student row is rewritten below, because
			# Frappe refuses to delete a User a Student still links to.
			updates["user"] = users[target.lower()]
			stats["relinked"] += 1
			if user and user.lower() in users:
				referenced_by.get(user.lower(), set()).discard(row.name)
				if not referenced_by.get(user.lower()):
					superseded = users[user.lower()]
		elif user and user.lower() in users:
			if frappe.db.get_value("User", users[user.lower()], "last_login"):
				# Somebody signs in with this; renaming it would take their
				# login away. Leave the record for a human to decide on.
				skipped.append(f"{school_id} (uses {user})")
				stats["skipped_in_use"] += 1
				continue
			rename_user(users[user.lower()], target, users)
			updates["user"] = target
			stats["renamed"] += 1
		else:
			updates["user"] = create_user(row, target)
			users[target.lower()] = target
			stats["created"] += 1

		# Written straight to the table: this is a surgical correction and must
		# not re-run Student.validate(), which would try to mint users again.
		frappe.db.set_value("Student", row.name, updates, update_modified=False)

		# Only now that nothing links to it can the old account be retired.
		if superseded:
			retire_superseded_user(superseded)

	if skipped:
		frappe.log_error(
			message="Left alone because their current login is in active use:\n"
			+ "\n".join(skipped),
			title="fix_student_email_school_id_mismatch: in-use logins",
		)

	return stats


def fix_applicants():
	"""Re-point Student Applicant rows at their own school ID.

	Scoped to existing students re-applying for the current intake, whose
	address was copied off the Student record wholesale. Earlier academic years
	are left as filed: those applications are closed history, and rewriting
	them would edit the record of what was actually submitted at the time.
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

	fixed = 0
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
		fixed += 1

	return fixed


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


def retire_superseded_user(name):
	"""Drop a student account nothing points at any more.

	Deletion is attempted so the address is free for reuse; an account that is
	still referenced elsewhere is disabled instead, which is enough to stop it
	being handed out again.
	"""
	if frappe.db.get_value("User", name, "last_login"):
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
			title=f"Could not delete superseded User {name}; disabled instead",
		)
