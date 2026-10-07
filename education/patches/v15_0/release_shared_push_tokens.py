import frappe


def execute():
	"""A device push token stays active only for the account signed in last.

	The same phone was registered under many accounts (up to dozens), all left
	active, so a notification for one student also reached every phone that any
	other account had ever been used on. Keep the most recently used active row
	per token and deactivate the rest.
	"""
	rows = frappe.db.sql(
		"""
		SELECT name, push_token, user, last_used, modified
		FROM `tabPush Token`
		WHERE is_active = 1
		ORDER BY push_token, COALESCE(last_used, modified) DESC, modified DESC
		""",
		as_dict=True,
	)

	seen = set()
	stale = []
	for row in rows:
		if row.push_token in seen:
			stale.append(row.name)
		else:
			seen.add(row.push_token)

	for start in range(0, len(stale), 500):
		frappe.db.sql(
			"UPDATE `tabPush Token` SET is_active = 0 WHERE name IN %(names)s",
			{"names": stale[start : start + 500]},
		)
