"""Read the class lists staff prepare for a new year.

A roster maps School ID -> Section. Two layouts are understood, in .xlsx or
.csv:

* one sheet with a School ID column and a Section column (the audit
  workbook's "All students" sheet is exactly this); and
* the class-list workbooks themselves, one sheet per section, where the
  sheet's name is the section ("LKG A", "Grade 10A").

Every sheet of a workbook is read, so a file can mix both.
"""

import io

import frappe
from frappe import _

from education.education.lifecycle.common import clean_spaces, normalize_school_id

SCHOOL_ID_HEADERS = {
	"schoolid",
	"rosterschoolid",
	"studentid",
	"schoolidnumber",
	"id",
	"idno",
	"idnumber",
}
SECTION_HEADERS = {"section", "studentgroup", "class", "group", "homeroom", "classsection"}
NAME_HEADERS = {"studentname", "name", "fullname", "rostername"}

# How far down a sheet to look for its header row.
HEADER_SCAN_ROWS = 10


def _header_key(value):
	return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def _find_columns(rows):
	"""Return (header_row_index, id_col, section_col, name_col) or None."""
	for index, row in enumerate(rows[:HEADER_SCAN_ROWS]):
		keys = [_header_key(cell) for cell in row]
		id_col = next((i for i, k in enumerate(keys) if k in SCHOOL_ID_HEADERS), None)
		if id_col is None:
			continue
		section_col = next((i for i, k in enumerate(keys) if k in SECTION_HEADERS), None)
		name_col = next((i for i, k in enumerate(keys) if k in NAME_HEADERS), None)
		return index, id_col, section_col, name_col
	return None


def _read_csv(content):
	"""Rows of a CSV file, whatever encoding and delimiter Excel saved it with."""
	import csv

	if isinstance(content, bytes):
		for encoding in ("utf-8-sig", "cp1252", "latin-1"):
			try:
				content = content.decode(encoding)
				break
			except UnicodeDecodeError:
				continue
	content = content.lstrip("\ufeff")
	try:
		dialect = csv.Sniffer().sniff(content[:4096], delimiters=",;\t")
	except csv.Error:
		dialect = csv.excel
	return [row for row in csv.reader(io.StringIO(content), dialect)]


def _sheets_from_file(file_url):
	"""Return [(sheet_name, rows)] for every sheet in an attached roster file."""
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		frappe.throw(_("The attached roster file could not be found. Attach it again."))
	file_doc = frappe.get_doc("File", file_name)
	name = (file_doc.file_name or file_url).lower()
	if not name.endswith((".csv", ".xlsx", ".xlsm")):
		frappe.throw(
			_("Upload the roster as an .xlsx or .csv file (old .xls files must be saved as .xlsx first).")
		)

	try:
		content = file_doc.get_content()
	except Exception:
		frappe.throw(_("The attached roster file could not be read. Attach it again."))

	if name.endswith(".csv"):
		return [("", _read_csv(content))]

	from openpyxl import load_workbook

	if isinstance(content, str):
		content = content.encode()
	try:
		workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
	except Exception:
		frappe.throw(_("The roster is not a valid .xlsx file. Open it in Excel and save it as .xlsx again."))
	try:
		return [
			(sheet.title, [list(row) for row in sheet.iter_rows(values_only=True)])
			for sheet in workbook.worksheets
		]
	finally:
		workbook.close()


def read_roster(file_url):
	"""Parse a roster file.

	Returns a dict::

	    {
	        "sections": {normalized_school_id: section},
	        "names": {normalized_school_id: name as written on the roster},
	        "conflicts": {normalized_school_id: [section, section, ...]},
	        "rows": int,          # rows that carried a School ID
	        "sheets": [sheet names that were used],
	    }

	A School ID listed under two different sections is a conflict: it is left
	out of ``sections`` so nobody is silently placed in the wrong class.
	"""
	seen = {}
	names = {}
	rows_read = 0
	sheets_used = []

	for sheet_name, rows in _sheets_from_file(file_url):
		found = _find_columns(rows)
		if not found:
			continue
		header_index, id_col, section_col, name_col = found
		if section_col is None and not sheet_name:
			continue

		used = False
		for row in rows[header_index + 1 :]:
			if id_col >= len(row):
				continue
			school_id = normalize_school_id(row[id_col])
			if not school_id or _header_key(row[id_col]) in SCHOOL_ID_HEADERS:
				continue
			section = row[section_col] if section_col is not None and section_col < len(row) else sheet_name
			section = clean_spaces(section)
			if not section or _header_key(section) in SECTION_HEADERS:
				continue
			rows_read += 1
			used = True
			seen.setdefault(school_id, set()).add(section)
			if name_col is not None and name_col < len(row) and row[name_col]:
				names.setdefault(school_id, clean_spaces(row[name_col]))
		if used:
			sheets_used.append(sheet_name or _("(single sheet)"))

	sections, conflicts = {}, {}
	for school_id, values in seen.items():
		# "Grade 10A" and "Grade 10 A" are the same class written two ways.
		distinct = {v.replace(" ", "").lower(): v for v in values}
		if len(distinct) == 1:
			sections[school_id] = next(iter(values))
		else:
			conflicts[school_id] = sorted(values)

	if not rows_read:
		frappe.msgprint(
			_(
				"No students were read from the roster. It needs a <b>School ID</b> column and a <b>Section</b> column "
				"(or one sheet per section, named after the section), with at least one filled row. "
				"Students are listed without roster sections."
			),
			title=_("Roster is empty"),
			indicator="orange",
		)

	return frappe._dict(
		sections=sections,
		names=names,
		conflicts=conflicts,
		rows=rows_read,
		sheets=sheets_used,
	)
