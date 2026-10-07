# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class StudentNotification(Document):
	"""One student's copy of a notification: their personal inbox entry.

	Created when an App Notification is sent, one per recipient student. The
	student app only ever reads these (its own), which is what keeps one
	family's messages away from another's, and it records whether the
	family has read it and whether the phone alert reached them.
	"""

	pass
