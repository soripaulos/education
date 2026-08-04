"""Delete the student accounts left behind by the school-address repair.

``fix_student_email_school_id_mismatch`` moved students onto the account that
carries their real school ID. It tried to delete the account each one was moved
off, but retired it *before* the Student row was rewritten, so Frappe still saw
a Student pointing at the account and refused ("You can disable this User
instead of deleting it"). Every one of them fell through to the disable branch.

Nothing references those accounts any more, so they can go. An account is only
removed when all of the following hold:

  * it is a Website User on the school domain - never a staff or system login;
  * it is already disabled;
  * it has **never been signed into** - anything with a login history is kept,
    because that is somebody's real account and its absence would be noticed;
  * no Student links to it, by either ``user`` or ``student_email_id``.

Anything that still fails to delete is left disabled and logged, so the site is
never left with dangling references.
"""

import frappe

DOMAIN = "@m.b.s"


def execute():
	candidates = frappe.db.sql(
		"""
		SELECT name
		FROM `tabUser`
		WHERE name LIKE %s
		  AND enabled = 0
		  AND user_type = 'Website User'
		  AND (last_login IS NULL OR last_login = '')
		""",
		(f"%{DOMAIN}",),
		pluck="name",
	)
	if not candidates:
		return

	# Anything a Student still points at stays, whichever field points at it.
	spoken_for = {
		value
		for value in frappe.db.sql_list(
			"""
			SELECT user FROM `tabStudent` WHERE user IS NOT NULL AND user != ''
			UNION
			SELECT student_email_id FROM `tabStudent`
			WHERE student_email_id IS NOT NULL AND student_email_id != ''
			"""
		)
	}

	deleted = 0
	kept = []
	for name in candidates:
		if name in spoken_for:
			continue
		try:
			# No `force`: a link that turns up here is a reason to stop, not
			# something to bulldoze past.
			frappe.delete_doc("User", name, ignore_permissions=True)
			deleted += 1
		except Exception:
			kept.append(name)

	frappe.db.commit()

	frappe.log_error(
		message=f"Deleted {deleted} superseded student account(s); {len(kept)} could not be removed.",
		title="purge_superseded_student_accounts",
	)
	if kept:
		frappe.log_error(
			message="Still linked somewhere, left disabled:\n" + "\n".join(kept),
			title="purge_superseded_student_accounts: retained",
		)
