# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

"""Desk-editable overrides for the student registration pages.

The deployed files under education/www stay the source of truth and the
fallback. When an override is switched on here and its HTML is non-empty, the
page's get_context() hands that HTML to the template, which renders it instead
of the file. Switching the override off restores the deployed file immediately,
so a bad edit is always one checkbox away from being undone.
"""

import frappe
from frappe import _
from frappe.model.document import Document

# page key -> (settings fieldname prefix, file under education/www)
PAGES = {
	"mbreg1825": ("mbreg1825", "mbreg1825.html"),
	"apply_dd": ("apply_dd", "apply_dd.html"),
}

# The Jinja wrapper the www templates are enclosed in. Kept here so
# "Load current page HTML" hands back the page itself, not the plumbing.
WRAPPER_FIRST_LINE = "{%- if html_override -%}{{ html_override | safe }}{%- else -%}"
WRAPPER_LAST_LINE = "{%- endif -%}"


class StudentApplicationPageSettings(Document):
	def validate(self):
		# An override that is on but empty would blank the page; treat it as off
		# and say so, rather than serving an empty document.
		for page, (prefix, _file) in PAGES.items():
			enabled = self.get(f"{prefix}_override_enabled")
			html = (self.get(f"{prefix}_html") or "").strip()
			if enabled and not html:
				self.set(f"{prefix}_override_enabled", 0)
				frappe.msgprint(
					_("The override for /{0} was switched off because its HTML is empty. The deployed page is being served.").format(
						page.replace("_", "-")
					),
					indicator="orange",
					alert=True,
				)


def _page_file_contents(page):
	"""Return the deployed file's page HTML, minus the Jinja override wrapper."""
	if page not in PAGES:
		frappe.throw(_("Unknown page: {0}").format(page))

	_prefix, filename = PAGES[page]
	path = frappe.get_app_path("education", "www", filename)
	with open(path, encoding="utf-8") as f:
		content = f.read()

	lines = content.splitlines()
	if lines and lines[0].strip() == WRAPPER_FIRST_LINE:
		lines = lines[1:]
	while lines and not lines[-1].strip():
		lines.pop()
	if lines and lines[-1].strip() == WRAPPER_LAST_LINE:
		lines.pop()
	return "\n".join(lines)


@frappe.whitelist()
def load_current_page_html(page):
	"""Return the deployed HTML for a page, to seed the Desk editor with."""
	frappe.only_for("System Manager")
	return _page_file_contents(page)


def get_page_html_override(page):
	"""Return the Desk override for a page, or "" to fall back to the file.

	Never raises: if the settings record does not exist yet (before the first
	save) or anything else goes wrong, the page must still render from its file.
	"""
	if page not in PAGES:
		return ""

	prefix, _filename = PAGES[page]
	try:
		enabled = frappe.db.get_single_value(
			"Student Application Page Settings", f"{prefix}_override_enabled"
		)
		if not enabled:
			return ""
		return (
			frappe.db.get_single_value("Student Application Page Settings", f"{prefix}_html")
			or ""
		)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(), "Student Application Page Settings override lookup failed"
		)
		return ""
