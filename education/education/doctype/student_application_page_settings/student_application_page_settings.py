# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

"""Desk-editable customisations for the student registration pages.

Three layers, smallest blast radius first:

``{page}_css`` / ``{page}_js``
    Injected into the deployed page. Nothing is replaced, so deploys keep
    reaching the page. This is the everyday tool.

``{page}_context_script``
    A Server Script whose ``context`` dict is merged into the page context, so
    values the Python computes can be added or overridden without a deploy. It
    runs through Frappe's sandboxed ``safe_exec``; arbitrary Python is never
    executed straight from a field on this form.

``{page}_override_enabled`` + ``{page}_html``
    Replaces the page wholesale. Powerful and the reason for the staleness
    tracking below: while an override is on, **deploying new code does not
    change that page**. The hash of the file the HTML was seeded from is kept
    so Desk and the page itself can say when the deployed version has moved on.
"""

import hashlib

import frappe
from frappe import _
from frappe.model.document import Document

# page key -> (settings fieldname prefix, file under education/www)
PAGES = {
	"mbreg1825": ("mbreg1825", "mbreg1825.html"),
	"apply_dd": ("apply_dd", "apply_dd.html"),
}

# Routes are only used for human-readable messages.
PAGE_ROUTES = {"mbreg1825": "/mbreg1825", "apply_dd": "/apply-dd"}

# The Jinja wrapper the www templates are enclosed in. Kept here so
# "Load current page HTML" hands back the page itself, not the plumbing.
WRAPPER_FIRST_LINE = "{%- if html_override -%}{{ html_override | safe }}{%- else -%}"
WRAPPER_LAST_LINE = "{%- endif -%}"


class StudentApplicationPageSettings(Document):
	def validate(self):
		for page, (prefix, _file) in PAGES.items():
			enabled = self.get(f"{prefix}_override_enabled")
			html = (self.get(f"{prefix}_html") or "").strip()

			# An override that is on but empty would blank the page; treat it as
			# off and say so, rather than serving an empty document.
			if enabled and not html:
				self.set(f"{prefix}_override_enabled", 0)
				frappe.msgprint(
					_("The override for {0} was switched off because its HTML is empty. The deployed page is being served.").format(
						PAGE_ROUTES.get(page, page)
					),
					indicator="orange",
					alert=True,
				)
				continue

			# A page whose Vue root is missing renders as a blank white screen
			# with no clue why, so refuse it rather than let it be published.
			if enabled and 'id="app"' not in html:
				frappe.throw(
					_('The override for {0} has no <div id="app"> element. The page would render blank, so it has not been saved.').format(
						PAGE_ROUTES.get(page, page)
					)
				)

			if enabled and self.is_override_stale(page):
				frappe.msgprint(
					_("Heads up: the deployed {0} page has changed since this HTML was loaded. While the override is on, those changes are not being served. Use <b>Load current page HTML</b> to pick them up.").format(
						PAGE_ROUTES.get(page, page)
					),
					indicator="orange",
				)

	def is_override_stale(self, page):
		return _is_override_stale(self, page)


def _is_override_stale(settings, page):
	"""True when the deployed file has moved on since the HTML was seeded.

	Module-level rather than a method so the render path never depends on the
	controller class being importable - a failure there would otherwise take
	the CSS/JS injection down with it.
	"""
	if page not in PAGES:
		return False
	prefix, _file = PAGES[page]
	stored = (settings.get(f"{prefix}_source_hash") or "").strip()
	if not stored:
		# Pasted in rather than loaded from the file - origin unknown, so
		# staleness cannot be claimed either way.
		return False
	return stored != _file_hash(page)


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


def _file_hash(page):
	"""Fingerprint of the deployed page, used to spot a stale override."""
	try:
		return hashlib.sha256(_page_file_contents(page).encode("utf-8")).hexdigest()
	except Exception:
		return ""


@frappe.whitelist()
def load_current_page_html(page):
	"""Return the deployed HTML for a page, with the fingerprint to store beside it."""
	frappe.only_for("System Manager")
	return {"html": _page_file_contents(page), "source_hash": _file_hash(page)}


@frappe.whitelist()
def get_page_status():
	"""Per-page override state, for the indicator on the settings form."""
	frappe.only_for("System Manager")
	settings = frappe.get_single("Student Application Page Settings")
	status = {}
	for page, (prefix, _file) in PAGES.items():
		enabled = bool(settings.get(f"{prefix}_override_enabled"))
		status[page] = {
			"route": PAGE_ROUTES.get(page, page),
			"override_enabled": enabled,
			"stale": bool(enabled and _is_override_stale(settings, page)),
			"has_css": bool((settings.get(f"{prefix}_css") or "").strip()),
			"has_js": bool((settings.get(f"{prefix}_js") or "").strip()),
			"context_script": settings.get(f"{prefix}_context_script") or "",
		}
	return status


def _run_context_script(script_name, page):
	"""Run a Server Script and return the ``context`` dict it built.

	Executed through Frappe's sandbox, the same way Server Scripts run
	everywhere else - this form never execs text from one of its own fields.
	"""
	try:
		from frappe.utils.safe_exec import safe_exec
	except Exception:
		return {}

	try:
		script_doc = frappe.get_doc("Server Script", script_name)
		if script_doc.get("disabled"):
			return {}
		_locals = {"page": page, "context": {}}
		safe_exec(script_doc.script, None, _locals)
		result = _locals.get("context")
		return result if isinstance(result, dict) else {}
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Student Application Page Settings: context script failed for {page}",
		)
		return {}


def _override_banner(page, stale):
	"""Strip shown on a page that is being served from Desk rather than code.

	Without it a stale override is invisible: the page looks normal while
	silently shadowing every deploy.
	"""
	route = PAGE_ROUTES.get(page, page)
	if stale:
		text = (
			f"This page is being served from <b>Student Application Page Settings</b>, "
			f"and the deployed {route} page has changed since that copy was saved. "
			f"Recent updates are <b>not</b> live here."
		)
		colour, background = "#991b1b", "#fee2e2"
	else:
		text = (
			f"This page is being served from <b>Student Application Page Settings</b>, "
			f"not from the deployed file. Turn the override off to go back to the deployed version."
		)
		colour, background = "#92400e", "#fef3c7"

	return (
		f'<div style="position:fixed;left:0;right:0;bottom:0;z-index:10030;'
		f'background:{background};color:{colour};font-size:12px;line-height:1.4;'
		f'padding:8px 14px;text-align:center;font-family:system-ui,sans-serif;'
		f'box-shadow:0 -1px 4px rgba(0,0,0,.12)">{text}</div>'
	)


def get_page_customisations(page):
	"""Everything Desk contributes to a page.

	Never raises: a page must still render if these settings are missing or
	broken, so every failure falls back to "no customisation".
	"""
	blank = {
		"html_override": "",
		"extra_head": "",
		"extra_body": "",
		"context_extra": {},
		"override_active": False,
		"override_stale": False,
	}
	if page not in PAGES:
		return blank

	prefix, _filename = PAGES[page]
	try:
		settings = frappe.get_single("Student Application Page Settings")
	except Exception:
		frappe.log_error(
			frappe.get_traceback(), "Student Application Page Settings lookup failed"
		)
		return blank

	try:
		enabled = bool(settings.get(f"{prefix}_override_enabled"))
		html = (settings.get(f"{prefix}_html") or "") if enabled else ""
		stale = bool(enabled and _is_override_stale(settings, page))

		css = (settings.get(f"{prefix}_css") or "").strip()
		js = (settings.get(f"{prefix}_js") or "").strip()

		extra_head = f"<style>\n{css}\n</style>" if css else ""
		extra_body = f"<script>\n{js}\n</script>" if js else ""
		if enabled and html:
			extra_body += _override_banner(page, stale)

		context_extra = {}
		script_name = settings.get(f"{prefix}_context_script")
		if script_name:
			context_extra = _run_context_script(script_name, page)

		return {
			"html_override": html,
			"extra_head": extra_head,
			"extra_body": extra_body,
			"context_extra": context_extra,
			"override_active": bool(enabled and html),
			"override_stale": stale,
		}
	except Exception:
		frappe.log_error(
			frappe.get_traceback(), f"Student Application Page Settings failed for {page}"
		)
		return blank


def apply_page_customisations(page, context):
	"""Fold the Desk customisations into a page's context.

	Both registration pages call this as the last step of get_context(), so the
	override/CSS/JS/context-script behaviour stays identical between them.
	"""
	custom = get_page_customisations(page)

	# The context script runs first so an override rendered below can use the
	# values it supplies.
	for key, value in (custom["context_extra"] or {}).items():
		context[key] = value

	context.page_extra_head = custom["extra_head"]
	context.page_extra_body = custom["extra_body"]

	override = custom["html_override"]
	if override:
		render_context = dict(context)
		# Blanked for this render only. HTML loaded from the deployed file
		# carries the placeholders, and the same markup is appended once below;
		# substituting here as well would inject everything twice.
		render_context["page_extra_head"] = ""
		render_context["page_extra_body"] = ""
		try:
			override = frappe.render_template(override, render_context)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(), f"{page} Desk override render failed"
			)
			override = ""

		if override:
			# Appended rather than left to the placeholders: stored HTML
			# predating this feature has none, and the staleness banner has to
			# reach exactly those older copies.
			override += custom["extra_head"] + custom["extra_body"]

	context.html_override = override
	return context


def get_page_html_override(page):
	"""Backwards-compatible accessor for the override HTML alone."""
	return get_page_customisations(page)["html_override"]
