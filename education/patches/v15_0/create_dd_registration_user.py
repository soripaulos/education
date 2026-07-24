"""Provision a dedicated, restricted user for the /apply-dd registration page.

Creates:
- Role "DD Student Registrar" (desk_access=0, i.e. no access to the Frappe
  backend/Desk at all - this account can only use website pages and
  whitelisted API calls it has doctype permission for).
- Doctype permissions for that role limited to exactly what the /apply-dd
  page's API calls touch: creating Student Applicant and Guardian records.
- User "Ermias Tesfaye" <ermiastas@gmail.com> with that role and no others
  besides the automatic "All" role that every Frappe user gets.

Idempotent: safe to re-run. On first run only, a random temporary password
is generated and printed to the migrate console (it is never written to
the repository) and a welcome email is sent to the user's address so they
can set their own password.
"""

import secrets

import frappe
from frappe.permissions import add_permission, update_permission_property

ROLE = "DD Student Registrar"
USER_EMAIL = "ermiastas@gmail.com"
USER_FIRST_NAME = "Ermias"
USER_LAST_NAME = "Tesfaye"

# (doctype, [ptypes to grant])
ROLE_PERMISSIONS = [
	("Student Applicant", ["create", "read", "write"]),
	("Guardian", ["create", "read", "write"]),
]


def execute():
	create_role()
	grant_role_permissions()
	create_user()


def create_role():
	if frappe.db.exists("Role", ROLE):
		return
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": ROLE,
			"desk_access": 0,
			"is_custom": 1,
		}
	).insert(ignore_permissions=True)


def grant_role_permissions():
	for doctype, ptypes in ROLE_PERMISSIONS:
		if not frappe.db.exists("DocType", doctype):
			continue
		# add_permission is idempotent: it only inserts a base DocPerm row
		# (with read=1) for the role if one doesn't already exist.
		add_permission(doctype, ROLE, 0)
		for ptype in ptypes:
			update_permission_property(doctype, ROLE, 0, ptype, 1)


def create_user():
	if frappe.db.exists("User", USER_EMAIL):
		# Already provisioned - just make sure the role is attached and no
		# password/email side effects run again on subsequent migrations.
		user = frappe.get_doc("User", USER_EMAIL)
		if ROLE not in [r.role for r in user.roles]:
			user.append("roles", {"role": ROLE})
			user.flags.ignore_permissions = True
			user.save(ignore_permissions=True)
		return

	temp_password = secrets.token_urlsafe(9)  # ~12 url-safe characters

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": USER_EMAIL,
			"first_name": USER_FIRST_NAME,
			"last_name": USER_LAST_NAME,
			"user_type": "Website User",
			"send_welcome_email": 1,
			"new_password": temp_password,
			"roles": [{"role": ROLE}],
		}
	)
	user.flags.ignore_permissions = True
	user.insert(ignore_permissions=True)

	print("\n" + "=" * 72)
	print(f"Created /apply-dd registration user: {USER_EMAIL}")
	print(f"Temporary password: {temp_password}")
	print(
		"A welcome/password-setup email has also been queued to that address "
		"(delivery depends on outgoing email being configured on this site)."
	)
	print(
		"This password is only ever shown here in the migrate console output "
		"- it is not stored in the repository. Share it with the user over a "
		"secure channel and have them change it on first login."
	)
	print("=" * 72 + "\n")
