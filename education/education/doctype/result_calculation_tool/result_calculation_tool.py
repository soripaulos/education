# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

"""
Result Calculation Tool
=======================

Calculates Student Term Reports (from Student Term Subject Results) and
Student Year Reports (from Student Term Reports) with:

- a preview / validation step that surfaces data-quality issues *before*
  anything is written (draft data, missing subjects, missing terms,
  inactive students, existing reports, excluded courses)
- configurable policies for every one of those situations
- course exclusions (course-level flag and per-run overrides) so subjects
  like Art in Kindergarten appear on reports without affecting averages
- per-student error isolation (one bad record doesn't abort the batch)
- background execution with live progress and a persistent
  Result Calculation Log documenting exactly what was done
"""

import json
import traceback

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime

# Draft data handling
DRAFT_IGNORE = "Ignore Draft Results"
DRAFT_INCLUDE = "Include Draft Results"
DRAFT_BLOCK = "Block if Drafts Exist"

# Missing subject handling (term calculation)
INCOMPLETE_CALCULATE = "Calculate with Available Subjects"
INCOMPLETE_SKIP = "Skip Students with Missing Subjects"
INCOMPLETE_BLOCK = "Block if Any Subject Missing"

# Missing term handling (year calculation)
MISSING_TERM_AVERAGE = "Average Available Terms"
MISSING_TERM_ZERO = "Treat Missing Terms as Zero"
MISSING_TERM_EXCLUDE = "Exclude Students with Missing Terms"
MISSING_TERM_BLOCK = "Block if Any Term Missing"

# Year average method
YEAR_AVG_TERM_BASED = "Average of Term Averages"
YEAR_AVG_COURSE_BASED = "Average of Course Year Percentages"

# Existing submitted report handling
EXISTING_REPLACE = "Replace Existing Submitted Reports"
EXISTING_SKIP = "Skip Existing Submitted Reports"

MAX_LOG_ENTRIES = 2000
PREVIEW_LIST_LIMIT = 30


class ResultCalculationTool(Document):
	pass


class CalculationBlocked(frappe.ValidationError):
	"""Raised when a configured policy blocks the calculation."""

	pass


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------


def _parse_params(params):
	if isinstance(params, str):
		params = json.loads(params)
	opts = frappe._dict(params or {})

	opts.calculation_type = opts.calculation_type or "Term Results"
	opts.result_action = opts.result_action or "Save as Draft"
	opts.submit_results = opts.result_action == "Save and Submit"
	opts.run_in_background = cint(opts.get("run_in_background", 1))
	opts.only_active_students = cint(opts.get("only_active_students", 1))
	opts.respect_course_exclusion_flags = cint(opts.get("respect_course_exclusion_flags", 1))
	opts.draft_result_handling = opts.draft_result_handling or DRAFT_IGNORE
	opts.incomplete_subject_policy = opts.incomplete_subject_policy or INCOMPLETE_CALCULATE
	opts.existing_report_policy = opts.existing_report_policy or EXISTING_REPLACE
	opts.missing_term_policy = opts.missing_term_policy or MISSING_TERM_AVERAGE
	opts.year_average_method = opts.year_average_method or YEAR_AVG_TERM_BASED

	opts.excluded_courses = _normalize_link_list(opts.get("excluded_courses"), "course")
	opts.terms_to_include = _normalize_link_list(opts.get("terms_to_include"), "academic_term")

	return opts


def _normalize_link_list(value, key):
	"""Accept a list of strings or a child-table list of dicts and return a list of names."""
	if not value:
		return []
	if isinstance(value, str):
		value = json.loads(value)
	names = []
	for item in value:
		if isinstance(item, dict):
			name = item.get(key)
		else:
			name = item
		if name and name not in names:
			names.append(name)
	return names


def _validate_params(opts):
	if opts.calculation_type not in ("Term Results", "Year Results"):
		frappe.throw(_("Invalid calculation type: {0}").format(opts.calculation_type))
	if not opts.academic_year:
		frappe.throw(_("Academic Year is required"))
	if opts.calculation_type == "Term Results" and not opts.semester:
		frappe.throw(_("Semester is required for Term Results calculation"))


def _check_permission():
	if frappe.session.user == "Administrator":
		return
	if not (
		frappe.has_permission("Student Term Report", "write")
		and frappe.has_permission("Student Year Report", "write")
	):
		frappe.throw(_("You are not permitted to calculate student results"), frappe.PermissionError)


# ---------------------------------------------------------------------------
# Shared data collection
# ---------------------------------------------------------------------------


def _get_excluded_courses(opts):
	"""Return (excluded_set, flagged_list, manual_list)."""
	flagged = []
	if opts.respect_course_exclusion_flags and frappe.db.has_column("Course", "exclude_from_result_average"):
		flagged = [
			c.name
			for c in frappe.get_all("Course", filters={"exclude_from_result_average": 1}, fields=["name"])
		]
	manual = list(opts.excluded_courses or [])
	return set(flagged) | set(manual), flagged, manual


def _get_docstatus_list(opts):
	if opts.draft_result_handling == DRAFT_INCLUDE:
		return [0, 1]
	return [1]


def _get_group_membership(groups):
	"""Return {group: {student: active(0/1)}} for the given student groups."""
	membership = {g: {} for g in groups}
	if not groups:
		return membership
	rows = frappe.get_all(
		"Student Group Student",
		filters={"parent": ["in", list(groups)], "parenttype": "Student Group"},
		fields=["parent", "student", "active"],
	)
	for row in rows:
		membership.setdefault(row.parent, {})[row.student] = cint(row.active)
	return membership


def _get_student_names(students):
	if not students:
		return {}
	rows = frappe.get_all(
		"Student", filters={"name": ["in", list(students)]}, fields=["name", "student_name"]
	)
	return {r.name: r.student_name or r.name for r in rows}


def _collect_term_data(opts):
	"""Gather and organize everything needed for a term calculation (also powers the preview)."""
	base_filters = {"semester": opts.semester, "academic_year": opts.academic_year}
	if opts.student_group:
		base_filters["student_group"] = opts.student_group

	draft_count = frappe.db.count(
		"Student Term Subject Result", dict(base_filters, docstatus=0)
	)
	submitted_count = frappe.db.count(
		"Student Term Subject Result", dict(base_filters, docstatus=1)
	)

	results = frappe.get_all(
		"Student Term Subject Result",
		filters=dict(base_filters, docstatus=["in", _get_docstatus_list(opts)]),
		fields=["name", "student", "student_group", "subject", "score", "max_score", "docstatus"],
	)

	excluded_courses, flagged_courses, manual_courses = _get_excluded_courses(opts)

	groups = {}
	all_students = set()
	for row in results:
		group = groups.setdefault(
			row.student_group, frappe._dict(students={}, universe=set(), all_subjects=set())
		)
		student = group.students.setdefault(row.student, {})
		subject = student.setdefault(
			row.subject, {"total_score": 0.0, "total_max_score": 0.0, "entries": 0}
		)
		subject["total_score"] += flt(row.score)
		subject["total_max_score"] += flt(row.max_score)
		subject["entries"] += 1
		group.all_subjects.add(row.subject)
		if row.subject not in excluded_courses:
			group.universe.add(row.subject)
		all_students.add(row.student)

	membership = _get_group_membership(list(groups))
	student_names = _get_student_names(all_students)

	# students in the group roster who have no results at all
	for group_name, group in groups.items():
		group.members_without_results = sorted(
			m
			for m, active in membership.get(group_name, {}).items()
			if active and m not in group.students
		)
		group.inactive_with_results = sorted(
			s
			for s in group.students
			if s in membership.get(group_name, {}) and not membership[group_name][s]
		)
		group.non_members_with_results = sorted(
			s for s in group.students if s not in membership.get(group_name, {})
		)
		# missing subjects per student, measured against the group's subject universe
		group.incomplete = {}
		for student, subjects in group.students.items():
			present = {s for s in subjects if s not in excluded_courses}
			missing = group.universe - present
			if missing:
				group.incomplete[student] = sorted(missing)

	existing_reports = _count_existing_reports(
		"Student Term Report",
		{"academic_year": opts.academic_year, "academic_term": opts.semester},
		opts.student_group,
	)

	return frappe._dict(
		results_count=len(results),
		draft_count=draft_count,
		submitted_count=submitted_count,
		excluded_courses=excluded_courses,
		flagged_courses=flagged_courses,
		manual_courses=manual_courses,
		groups=groups,
		membership=membership,
		student_names=student_names,
		existing_reports=existing_reports,
	)


def _collect_year_data(opts):
	"""Gather and organize everything needed for a year calculation (also powers the preview)."""
	base_filters = {"academic_year": opts.academic_year}
	if opts.student_group:
		base_filters["student_group"] = opts.student_group

	draft_count = frappe.db.count("Student Term Report", dict(base_filters, docstatus=0))
	submitted_count = frappe.db.count("Student Term Report", dict(base_filters, docstatus=1))

	# ordered list of the academic year's terms
	year_terms = [
		t.name
		for t in frappe.get_all(
			"Academic Term",
			filters={"academic_year": opts.academic_year},
			fields=["name"],
			order_by="term_start_date asc, name asc",
		)
	]

	reports = frappe.get_all(
		"Student Term Report",
		filters=dict(base_filters, docstatus=["in", _get_docstatus_list(opts)]),
		fields=[
			"name",
			"student",
			"student_name",
			"student_group",
			"academic_term",
			"term_average",
			"docstatus",
		],
	)

	detected_terms = {r.academic_term for r in reports}
	foreign_terms = []

	if opts.terms_to_include:
		expected_terms = list(opts.terms_to_include)
		foreign_terms = [t for t in expected_terms if year_terms and t not in year_terms]
	else:
		# auto-detect: every term of the year that has report data, in calendar order
		expected_terms = [t for t in year_terms if t in detected_terms]
		# terms with data that aren't linked to this academic year (data-entry mistakes)
		expected_terms += sorted(t for t in detected_terms if t not in year_terms)

	excluded_courses, flagged_courses, manual_courses = _get_excluded_courses(opts)

	groups = {}
	for row in reports:
		if row.academic_term not in expected_terms:
			continue
		group = groups.setdefault(row.student_group, frappe._dict(students={}))
		student = group.students.setdefault(
			row.student, frappe._dict(student_name=row.student_name, terms={})
		)
		student.terms[row.academic_term] = frappe._dict(
			report=row.name, term_average=flt(row.term_average)
		)

	membership = _get_group_membership(list(groups))

	term_report_counts = {}
	for term in expected_terms:
		term_report_counts[term] = sum(
			1
			for g in groups.values()
			for s in g.students.values()
			if term in s.terms
		)

	for group_name, group in groups.items():
		group.incomplete = {}
		for student, data in group.students.items():
			missing = [t for t in expected_terms if t not in data.terms]
			if missing:
				group.incomplete[student] = missing
		group.inactive_with_results = sorted(
			s
			for s in group.students
			if s in membership.get(group_name, {}) and not membership[group_name][s]
		)

	existing_reports = _count_existing_reports(
		"Student Year Report", {"academic_year": opts.academic_year}, opts.student_group
	)

	return frappe._dict(
		reports_count=len(reports),
		draft_count=draft_count,
		submitted_count=submitted_count,
		expected_terms=expected_terms,
		year_terms=year_terms,
		foreign_terms=foreign_terms,
		term_report_counts=term_report_counts,
		excluded_courses=excluded_courses,
		flagged_courses=flagged_courses,
		manual_courses=manual_courses,
		groups=groups,
		membership=membership,
		existing_reports=existing_reports,
	)


def _count_existing_reports(doctype, filters, student_group=None):
	if student_group:
		filters = dict(filters, student_group=student_group)
	return {
		"draft": frappe.db.count(doctype, dict(filters, docstatus=0)),
		"submitted": frappe.db.count(doctype, dict(filters, docstatus=1)),
	}


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


def _cap(items):
	items = list(items)
	return {"items": items[:PREVIEW_LIST_LIMIT], "more": max(0, len(items) - PREVIEW_LIST_LIMIT), "total": len(items)}


@frappe.whitelist()
def preview_calculation(params):
	"""Validate the calculation parameters and report every data-quality issue
	that would affect the run, without writing anything."""
	_check_permission()
	opts = _parse_params(params)
	_validate_params(opts)

	if opts.calculation_type == "Term Results":
		return _preview_term(opts)
	return _preview_year(opts)


def _preview_term(opts):
	data = _collect_term_data(opts)
	issues = []

	if not data.results_count:
		issues.append(
			{
				"level": "error",
				"message": _("No {0} subject results found for the selected term. Nothing to calculate.").format(
					_("submitted") if opts.draft_result_handling != DRAFT_INCLUDE else _("submitted or draft")
				),
			}
		)

	if data.draft_count:
		if opts.draft_result_handling == DRAFT_BLOCK:
			issues.append(
				{
					"level": "error",
					"message": _(
						"{0} subject results are still in Draft and the draft policy is set to block. Submit or delete them first."
					).format(data.draft_count),
				}
			)
		elif opts.draft_result_handling == DRAFT_INCLUDE:
			issues.append(
				{
					"level": "warning",
					"message": _("{0} draft subject results will be INCLUDED in the calculation.").format(
						data.draft_count
					),
				}
			)
		else:
			issues.append(
				{
					"level": "warning",
					"message": _(
						"{0} subject results are still in Draft and will be ignored. Scores in those drafts will NOT be counted."
					).format(data.draft_count),
				}
			)

	total_incomplete = sum(len(g.incomplete) for g in data.groups.values())
	if total_incomplete:
		level = "error" if opts.incomplete_subject_policy == INCOMPLETE_BLOCK else "warning"
		issues.append(
			{
				"level": level,
				"message": _(
					"{0} student(s) are missing results for subjects that others in their group have. Policy: {1}."
				).format(total_incomplete, _(opts.incomplete_subject_policy)),
			}
		)

	total_inactive = sum(len(g.inactive_with_results) for g in data.groups.values())
	if total_inactive:
		issues.append(
			{
				"level": "warning",
				"message": _(
					"{0} student(s) with results are marked inactive in their student group{1}."
				).format(
					total_inactive,
					_(" and will be skipped") if opts.only_active_students else _(" but will still be calculated"),
				),
			}
		)

	total_no_results = sum(len(g.members_without_results) for g in data.groups.values())
	if total_no_results:
		issues.append(
			{
				"level": "warning",
				"message": _(
					"{0} active student(s) in the selected group(s) have no subject results at all and will get no report."
				).format(total_no_results),
			}
		)

	total_non_members = sum(len(g.non_members_with_results) for g in data.groups.values())
	if total_non_members:
		issues.append(
			{
				"level": "warning",
				"message": _(
					"{0} student(s) have results in a group they are not listed in (check the Student Group rosters)."
				).format(total_non_members),
			}
		)

	if data.existing_reports["submitted"]:
		issues.append(
			{
				"level": "warning",
				"message": _("{0} submitted term report(s) already exist. Policy: {1}.").format(
					data.existing_reports["submitted"], _(opts.existing_report_policy)
				),
			}
		)

	names = data.student_names
	group_details = []
	for group_name in sorted(data.groups):
		g = data.groups[group_name]
		group_details.append(
			{
				"group": group_name,
				"students_with_results": len(g.students),
				"subjects": sorted(g.all_subjects),
				"included_subjects": sorted(g.universe),
				"excluded_subjects": sorted(g.all_subjects & data.excluded_courses),
				"incomplete_students": _cap(
					[
						{"student": s, "student_name": names.get(s, s), "missing": missing}
						for s, missing in sorted(g.incomplete.items())
					]
				),
				"members_without_results": _cap([names.get(s, s) for s in g.members_without_results]),
				"inactive_with_results": _cap([names.get(s, s) for s in g.inactive_with_results]),
				"non_members_with_results": _cap([names.get(s, s) for s in g.non_members_with_results]),
			}
		)

	total_students = sum(len(g.students) for g in data.groups.values())

	return {
		"calculation_type": opts.calculation_type,
		"can_proceed": not any(i["level"] == "error" for i in issues),
		"total_students": total_students,
		"total_groups": len(data.groups),
		"results_count": data.results_count,
		"submitted_count": data.submitted_count,
		"draft_count": data.draft_count,
		"excluded_courses": sorted(data.excluded_courses),
		"flagged_courses": sorted(data.flagged_courses),
		"manual_courses": sorted(data.manual_courses),
		"existing_reports": data.existing_reports,
		"issues": issues,
		"groups": group_details,
	}


def _preview_year(opts):
	data = _collect_year_data(opts)
	issues = []

	if not data.reports_count:
		issues.append(
			{
				"level": "error",
				"message": _(
					"No submitted term reports found for the selected academic year. Run the Term Results calculation first."
				),
			}
		)

	if not data.expected_terms:
		issues.append(
			{
				"level": "error",
				"message": _("Could not determine which terms make up this academic year. Select them explicitly under Year Calculation Options."),
			}
		)
	elif len(data.expected_terms) == 1:
		issues.append(
			{
				"level": "warning",
				"message": _(
					"Only one term ({0}) has term reports. The year report will be based on a single term."
				).format(data.expected_terms[0]),
			}
		)

	if data.foreign_terms:
		issues.append(
			{
				"level": "warning",
				"message": _("Selected term(s) {0} do not belong to academic year {1}.").format(
					", ".join(data.foreign_terms), opts.academic_year
				),
			}
		)

	if data.draft_count:
		if opts.draft_result_handling == DRAFT_BLOCK:
			issues.append(
				{
					"level": "error",
					"message": _(
						"{0} term report(s) are still in Draft and the draft policy is set to block. Submit or delete them first."
					).format(data.draft_count),
				}
			)
		elif opts.draft_result_handling == DRAFT_INCLUDE:
			issues.append(
				{
					"level": "warning",
					"message": _("{0} draft term report(s) will be INCLUDED in the year calculation.").format(
						data.draft_count
					),
				}
			)
		else:
			issues.append(
				{
					"level": "warning",
					"message": _(
						"{0} term report(s) are still in Draft and will be ignored for the year calculation."
					).format(data.draft_count),
				}
			)

	total_incomplete = sum(len(g.incomplete) for g in data.groups.values())
	if total_incomplete:
		level = "error" if opts.missing_term_policy == MISSING_TERM_BLOCK else "warning"
		issues.append(
			{
				"level": level,
				"message": _(
					"{0} student(s) do not have term reports for every expected term (joined late, left early, or the term calculation wasn't run for them). Policy: {1}."
				).format(total_incomplete, _(opts.missing_term_policy)),
			}
		)

	total_inactive = sum(len(g.inactive_with_results) for g in data.groups.values())
	if total_inactive:
		issues.append(
			{
				"level": "warning",
				"message": _("{0} student(s) with term reports are marked inactive in their student group{1}.").format(
					total_inactive,
					_(" and will be skipped") if opts.only_active_students else _(" but will still be calculated"),
				),
			}
		)

	if data.existing_reports["submitted"]:
		issues.append(
			{
				"level": "warning",
				"message": _("{0} submitted year report(s) already exist. Policy: {1}.").format(
					data.existing_reports["submitted"], _(opts.existing_report_policy)
				),
			}
		)

	group_details = []
	for group_name in sorted(data.groups):
		g = data.groups[group_name]
		group_details.append(
			{
				"group": group_name,
				"students_with_results": len(g.students),
				"incomplete_students": _cap(
					[
						{
							"student": s,
							"student_name": g.students[s].student_name or s,
							"missing": missing,
							"present": sorted(g.students[s].terms),
						}
						for s, missing in sorted(g.incomplete.items())
					]
				),
				"inactive_with_results": _cap(
					[g.students[s].student_name or s for s in g.inactive_with_results]
				),
			}
		)

	total_students = sum(len(g.students) for g in data.groups.values())

	return {
		"calculation_type": opts.calculation_type,
		"can_proceed": not any(i["level"] == "error" for i in issues),
		"total_students": total_students,
		"total_groups": len(data.groups),
		"reports_count": data.reports_count,
		"submitted_count": data.submitted_count,
		"draft_count": data.draft_count,
		"expected_terms": data.expected_terms,
		"term_report_counts": data.term_report_counts,
		"excluded_courses": sorted(data.excluded_courses),
		"flagged_courses": sorted(data.flagged_courses),
		"manual_courses": sorted(data.manual_courses),
		"existing_reports": data.existing_reports,
		"issues": issues,
		"groups": group_details,
	}


# ---------------------------------------------------------------------------
# Execution entry points
# ---------------------------------------------------------------------------


@frappe.whitelist()
def start_calculation(params):
	"""Create a Result Calculation Log and run the calculation (in the
	background by default). Returns the log name immediately."""
	_check_permission()
	opts = _parse_params(params)
	_validate_params(opts)

	log = frappe.get_doc(
		{
			"doctype": "Result Calculation Log",
			"status": "Queued",
			"calculation_type": opts.calculation_type,
			"result_action": opts.result_action,
			"academic_year": opts.academic_year,
			"semester": opts.semester if opts.calculation_type == "Term Results" else None,
			"student_group": opts.student_group,
			"started_by": frappe.session.user,
			"options_json": frappe.as_json(
				{k: v for k, v in opts.items() if k not in ("preview_html", "logs_html")}, indent=1
			),
		}
	)
	log.insert(ignore_permissions=True)

	if opts.run_in_background:
		frappe.enqueue(
			execute_calculation,
			queue="long",
			timeout=7200,
			job_name=f"result_calculation_{log.name}",
			log_name=log.name,
			enqueue_after_commit=True,
		)
		return {"log_name": log.name, "queued": True}

	result = execute_calculation(log.name)
	result["log_name"] = log.name
	result["queued"] = False
	return result


def execute_calculation(log_name):
	"""Job body: run the calculation described by the given log document."""
	calculator = _Calculator(log_name)
	return calculator.run()


@frappe.whitelist()
def get_recent_logs(limit=5):
	"""Recent calculation runs, for display on the tool page."""
	_check_permission()
	return frappe.get_all(
		"Result Calculation Log",
		fields=[
			"name",
			"status",
			"calculation_type",
			"academic_year",
			"semester",
			"student_group",
			"started_at",
			"completed_at",
			"total_students",
			"succeeded",
			"skipped",
			"failed",
			"warnings",
			"summary",
		],
		order_by="creation desc",
		limit_page_length=cint(limit) or 5,
	)


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------


class _Calculator:
	def __init__(self, log_name):
		self.log = frappe.get_doc("Result Calculation Log", log_name)
		self.opts = _parse_params(self.log.options_json)
		self.counters = frappe._dict(
			processed=0,
			succeeded=0,
			skipped=0,
			failed=0,
			warnings=0,
			created=0,
			updated=0,
			replaced=0,
			submitted=0,
		)
		self.suppressed_entries = 0
		self.total_students = 0

	# -- logging helpers ----------------------------------------------------

	def add_entry(self, level, message, student=None, student_name=None, student_group=None, course=None):
		if level == "Warning":
			self.counters.warnings += 1
		if len(self.log.entries) >= MAX_LOG_ENTRIES:
			self.suppressed_entries += 1
			return
		self.log.append(
			"entries",
			{
				"level": level,
				"student": student,
				"student_name": student_name,
				"student_group": student_group,
				"course": course,
				"message": message,
			},
		)

	def save_log(self, commit=False):
		c = self.counters
		self.log.processed_students = c.processed
		self.log.succeeded = c.succeeded
		self.log.skipped = c.skipped
		self.log.failed = c.failed
		self.log.warnings = c.warnings
		self.log.reports_created = c.created
		self.log.reports_updated = c.updated
		self.log.reports_replaced = c.replaced
		self.log.reports_submitted = c.submitted
		self.log.total_students = self.total_students
		self.log.save(ignore_permissions=True)
		if commit:
			frappe.db.commit()

	def publish_progress(self, description):
		try:
			percent = (self.counters.processed / self.total_students * 100) if self.total_students else 0
			frappe.publish_progress(
				percent,
				title=_("Calculating {0}").format(_(self.opts.calculation_type)),
				description=description,
			)
			frappe.publish_realtime(
				"result_calculation_progress",
				{
					"log": self.log.name,
					"percent": percent,
					"processed": self.counters.processed,
					"total": self.total_students,
					"description": description,
				},
				user=self.log.started_by,
			)
		except Exception:
			pass  # progress reporting must never break the calculation

	# -- main flow -----------------------------------------------------------

	def run(self):
		self.log.status = "In Progress"
		self.log.started_at = now_datetime()
		self.save_log(commit=True)

		try:
			if self.opts.calculation_type == "Term Results":
				self.run_term()
			else:
				self.run_year()
			self.finish()
		except CalculationBlocked as e:
			self.fail(str(e))
		except Exception:
			self.fail(_("Unexpected error"), traceback.format_exc())

		frappe.publish_realtime(
			"result_calculation_complete",
			{"log": self.log.name, "status": self.log.status, "summary": self.log.summary},
			user=self.log.started_by,
		)
		return {"status": self.log.status, "summary": self.log.summary}

	def finish(self):
		c = self.counters
		if self.suppressed_entries:
			self.add_entry(
				"Info",
				_("{0} further log entries were suppressed (limit of {1} reached).").format(
					self.suppressed_entries, MAX_LOG_ENTRIES
				),
			)
		self.log.status = (
			"Completed with Warnings" if (c.failed or c.warnings or c.skipped) else "Completed"
		)
		self.log.completed_at = now_datetime()

		parts = [
			_("{0} of {1} students processed").format(c.succeeded, self.total_students),
			_("{0} reports created").format(c.created),
		]
		if c.updated:
			parts.append(_("{0} drafts updated").format(c.updated))
		if c.replaced:
			parts.append(_("{0} submitted reports replaced").format(c.replaced))
		if c.submitted:
			parts.append(_("{0} submitted").format(c.submitted))
		if c.skipped:
			parts.append(_("{0} skipped").format(c.skipped))
		if c.failed:
			parts.append(_("{0} FAILED").format(c.failed))
		if c.warnings:
			parts.append(_("{0} warnings").format(c.warnings))
		self.log.summary = ", ".join(parts)
		self.save_log(commit=True)

	def fail(self, message, tb=None):
		frappe.db.rollback()
		self.log.status = "Failed"
		self.log.completed_at = now_datetime()
		self.log.summary = message
		if tb:
			self.add_entry("Error", f"{message}\n{tb[-1500:]}")
			frappe.log_error(
				title=f"Result Calculation {self.log.name} failed", message=tb
			)
		else:
			self.add_entry("Error", message)
		self.save_log(commit=True)

	# -- term calculation ----------------------------------------------------

	def run_term(self):
		opts = self.opts
		data = _collect_term_data(opts)

		if not data.results_count:
			raise CalculationBlocked(_("No usable subject results found for the selected term"))

		if data.draft_count and opts.draft_result_handling == DRAFT_BLOCK:
			raise CalculationBlocked(
				_("{0} subject results are still in Draft (policy: block until all are submitted)").format(
					data.draft_count
				)
			)

		if data.draft_count and opts.draft_result_handling == DRAFT_IGNORE:
			self.add_entry(
				"Warning",
				_("{0} draft subject results were ignored. Their scores are not counted.").format(
					data.draft_count
				),
			)
		if data.draft_count and opts.draft_result_handling == DRAFT_INCLUDE:
			self.add_entry(
				"Warning",
				_("{0} draft subject results were included in the calculation.").format(data.draft_count),
			)

		total_incomplete = sum(len(g.incomplete) for g in data.groups.values())
		if total_incomplete and opts.incomplete_subject_policy == INCOMPLETE_BLOCK:
			raise CalculationBlocked(
				_("{0} student(s) have missing subject results (policy: block). Run the preview for details.").format(
					total_incomplete
				)
			)

		if data.excluded_courses:
			self.add_entry(
				"Info",
				_("Courses excluded from averages: {0}").format(", ".join(sorted(data.excluded_courses))),
			)

		self.total_students = sum(len(g.students) for g in data.groups.values())
		names = data.student_names

		for group_name in sorted(data.groups):
			group = data.groups[group_name]
			group_membership = data.membership.get(group_name, {})
			submitted_names = []

			for student in sorted(group.students, key=lambda s: names.get(s, s)):
				student_name = names.get(student, student)
				self.counters.processed += 1
				self.publish_progress(f"{student_name} ({group_name})")

				# roster checks
				if student in group_membership and not group_membership[student]:
					if opts.only_active_students:
						self.counters.skipped += 1
						self.add_entry(
							"Skipped",
							_("Student is inactive in the student group; no report generated."),
							student,
							student_name,
							group_name,
						)
						continue
					self.add_entry(
						"Warning",
						_("Student is inactive in the student group but was calculated anyway."),
						student,
						student_name,
						group_name,
					)
				elif student not in group_membership:
					self.add_entry(
						"Warning",
						_("Student has results for this group but is not on its roster."),
						student,
						student_name,
						group_name,
					)

				missing = group.incomplete.get(student)
				if missing:
					if opts.incomplete_subject_policy == INCOMPLETE_SKIP:
						self.counters.skipped += 1
						self.add_entry(
							"Skipped",
							_("Missing results for: {0}").format(", ".join(missing)),
							student,
							student_name,
							group_name,
						)
						continue
					self.add_entry(
						"Warning",
						_("Missing results for: {0}. Average uses available subjects only.").format(
							", ".join(missing)
						),
						student,
						student_name,
						group_name,
					)

				frappe.db.savepoint("rct_student")
				try:
					report, action = self.upsert_term_report(
						student, student_name, group_name, group.students[student], data.excluded_courses
					)
					if action == "skipped_existing":
						self.counters.skipped += 1
						self.add_entry(
							"Skipped",
							_("A submitted term report already exists (policy: skip existing)."),
							student,
							student_name,
							group_name,
						)
						continue
					self.counters[
						{"created": "created", "updated": "updated", "replaced": "replaced"}[action]
					] += 1
					if opts.submit_results:
						submitted_names.append(report.name)
					self.counters.succeeded += 1
					self.add_entry(
						"Success",
						_("Term average {0}% from {1} subjects ({2}).").format(
							round(flt(report.term_average), 2),
							len([r for r in report.course_summary if not cint(r.excluded_from_average)]),
							_(action),
						),
						student,
						student_name,
						group_name,
					)
				except Exception:
					frappe.db.rollback(save_point="rct_student")
					self.counters.failed += 1
					self.add_entry(
						"Error",
						_("Failed: {0}").format(traceback.format_exc()[-1000:]),
						student,
						student_name,
						group_name,
					)

			# rank everything in the group (drafts + already-submitted survivors)
			_apply_ranks(
				"Student Term Report",
				{
					"academic_year": opts.academic_year,
					"academic_term": opts.semester,
					"student_group": group_name,
					"docstatus": ["in", [0, 1]],
				},
				"term_average",
			)

			if opts.submit_results:
				self.submit_reports("Student Term Report", submitted_names, group_name)

			self.save_log(commit=True)

	def upsert_term_report(self, student, student_name, group_name, subjects_data, excluded_courses):
		opts = self.opts
		doc, action = self.get_report_shell(
			"Student Term Report",
			{
				"student": student,
				"academic_year": opts.academic_year,
				"academic_term": opts.semester,
				"student_group": group_name,
			},
		)
		if action == "skipped_existing":
			return None, action

		doc.student = student
		doc.student_name = student_name
		doc.academic_year = opts.academic_year
		doc.academic_term = opts.semester
		doc.student_group = group_name
		doc.course_summary = []

		included_percentages = []
		for subject in sorted(subjects_data):
			totals = subjects_data[subject]
			max_score = flt(totals["total_max_score"])
			excluded = subject in excluded_courses
			if not excluded and max_score <= 0:
				# unusable data: show the row but keep it out of the average
				excluded = True
				self.add_entry(
					"Warning",
					_("Maximum score is 0 for {0}; the subject was left out of the average.").format(subject),
					student,
					student_name,
					group_name,
					course=subject,
				)
			percentage = (flt(totals["total_score"]) / max_score * 100) if max_score else 0
			doc.append(
				"course_summary",
				{
					"course": subject,
					"total_score_for_term": flt(totals["total_score"]),
					"total_maximum_score": max_score,
					"percentage": percentage,
					"excluded_from_average": cint(excluded),
				},
			)
			if not excluded:
				included_percentages.append(percentage)

		# Set the term average here in the tool rather than relying on the
		# Student Term Report controller. That doctype is a Custom DocType on
		# the site, so its Python controller (validate -> calculate_term_average)
		# does not run; without this, term_average would stay 0.
		doc.term_average = (
			sum(included_percentages) / len(included_percentages) if included_percentages else 0
		)

		doc.save(ignore_permissions=True)
		return doc, action

	# -- year calculation ------------------------------------------------------

	def run_year(self):
		opts = self.opts
		data = _collect_year_data(opts)

		if not data.reports_count:
			raise CalculationBlocked(
				_("No usable term reports found for the selected academic year. Run the Term Results calculation first.")
			)
		if not data.expected_terms:
			raise CalculationBlocked(
				_("Could not determine the terms of the academic year. Select them explicitly in Year Calculation Options.")
			)

		if data.draft_count and opts.draft_result_handling == DRAFT_BLOCK:
			raise CalculationBlocked(
				_("{0} term reports are still in Draft (policy: block until all are submitted)").format(
					data.draft_count
				)
			)
		if data.draft_count and opts.draft_result_handling == DRAFT_IGNORE:
			self.add_entry(
				"Warning",
				_("{0} draft term reports were ignored for the year calculation.").format(data.draft_count),
			)
		if data.draft_count and opts.draft_result_handling == DRAFT_INCLUDE:
			self.add_entry(
				"Warning",
				_("{0} draft term reports were included in the year calculation.").format(data.draft_count),
			)

		total_incomplete = sum(len(g.incomplete) for g in data.groups.values())
		if total_incomplete and opts.missing_term_policy == MISSING_TERM_BLOCK:
			raise CalculationBlocked(
				_("{0} student(s) have missing terms (policy: block). Run the preview for details.").format(
					total_incomplete
				)
			)

		self.add_entry(
			"Info",
			_("Terms included in the year: {0}").format(", ".join(data.expected_terms)),
		)
		if data.excluded_courses:
			self.add_entry(
				"Info",
				_("Courses excluded from averages: {0}").format(", ".join(sorted(data.excluded_courses))),
			)

		# bulk-load course summaries of every involved term report
		all_report_names = [
			t.report
			for g in data.groups.values()
			for s in g.students.values()
			for t in s.terms.values()
		]
		course_rows = {}
		if all_report_names:
			for row in frappe.get_all(
				"Course Term Summary",
				filters={"parent": ["in", all_report_names], "parenttype": "Student Term Report"},
				fields=["parent", "course", "total_score_for_term", "total_maximum_score"],
			):
				course_rows.setdefault(row.parent, []).append(row)

		self.total_students = sum(len(g.students) for g in data.groups.values())
		expected_terms = data.expected_terms

		for group_name in sorted(data.groups):
			group = data.groups[group_name]
			group_membership = data.membership.get(group_name, {})
			submitted_names = []

			for student in sorted(
				group.students, key=lambda s: group.students[s].student_name or s
			):
				sdata = group.students[student]
				student_name = sdata.student_name or student
				self.counters.processed += 1
				self.publish_progress(f"{student_name} ({group_name})")

				if (
					opts.only_active_students
					and student in group_membership
					and not group_membership[student]
				):
					self.counters.skipped += 1
					self.add_entry(
						"Skipped",
						_("Student is inactive in the student group; no year report generated."),
						student,
						student_name,
						group_name,
					)
					continue

				missing_terms = [t for t in expected_terms if t not in sdata.terms]
				if missing_terms and opts.missing_term_policy == MISSING_TERM_EXCLUDE:
					self.counters.skipped += 1
					self.add_entry(
						"Skipped",
						_("Missing term(s): {0} (policy: exclude students with missing terms).").format(
							", ".join(missing_terms)
						),
						student,
						student_name,
						group_name,
					)
					continue

				frappe.db.savepoint("rct_student")
				try:
					report, action = self.upsert_year_report(
						student,
						student_name,
						group_name,
						sdata,
						expected_terms,
						missing_terms,
						course_rows,
						data.excluded_courses,
					)
					if action == "skipped_existing":
						self.counters.skipped += 1
						self.add_entry(
							"Skipped",
							_("A submitted year report already exists (policy: skip existing)."),
							student,
							student_name,
							group_name,
						)
						continue
					self.counters[
						{"created": "created", "updated": "updated", "replaced": "replaced"}[action]
					] += 1
					if opts.submit_results:
						submitted_names.append(report.name)
					self.counters.succeeded += 1
					message = _("Year average {0}% from {1} of {2} terms ({3}).").format(
						round(flt(report.year_average), 2),
						len(sdata.terms),
						len(expected_terms),
						_(action),
					)
					if missing_terms:
						message += " " + _("Missing: {0}. Policy applied: {1}.").format(
							", ".join(missing_terms), _(opts.missing_term_policy)
						)
						self.add_entry("Warning", message, student, student_name, group_name)
					else:
						self.add_entry("Success", message, student, student_name, group_name)
				except Exception:
					frappe.db.rollback(save_point="rct_student")
					self.counters.failed += 1
					self.add_entry(
						"Error",
						_("Failed: {0}").format(traceback.format_exc()[-1000:]),
						student,
						student_name,
						group_name,
					)

			_apply_ranks(
				"Student Year Report",
				{
					"academic_year": opts.academic_year,
					"student_group": group_name,
					"docstatus": ["in", [0, 1]],
				},
				"year_average",
			)

			if opts.submit_results:
				self.submit_reports("Student Year Report", submitted_names, group_name)

			self.save_log(commit=True)

	def upsert_year_report(
		self,
		student,
		student_name,
		group_name,
		sdata,
		expected_terms,
		missing_terms,
		course_rows,
		excluded_courses,
	):
		opts = self.opts
		doc, action = self.get_report_shell(
			"Student Year Report",
			{
				"student": student,
				"academic_year": opts.academic_year,
				"student_group": group_name,
			},
		)
		if action == "skipped_existing":
			return None, action

		doc.student = student
		doc.student_name = student_name
		doc.academic_year = opts.academic_year
		doc.student_group = group_name

		# course year summary across the student's term reports
		course_data = {}
		for term, tinfo in sdata.terms.items():
			for row in course_rows.get(tinfo.report, []):
				cd = course_data.setdefault(
					row.course, {"total_score": 0.0, "max_score": 0.0, "count": 0}
				)
				cd["total_score"] += flt(row.total_score_for_term)
				cd["max_score"] += flt(row.total_maximum_score)
				cd["count"] += 1

		doc.course_year_summary = []
		course_percentages = []
		for course in sorted(course_data):
			cd = course_data[course]
			percentage = (cd["total_score"] / cd["max_score"] * 100) if cd["max_score"] else 0
			excluded = course in excluded_courses or not cd["max_score"]
			doc.append(
				"course_year_summary",
				{
					"course": course,
					"total_year_score": cd["total_score"],
					"total_year_max_score": cd["max_score"],
					"year_average_percentage": percentage,
					"terms_count": cd["count"],
					"excluded_from_average": cint(excluded),
				},
			)
			if not excluded:
				course_percentages.append(percentage)

		# year average
		term_averages = [flt(sdata.terms[t].term_average) for t in expected_terms if t in sdata.terms]
		if opts.year_average_method == YEAR_AVG_COURSE_BASED:
			year_average = (
				sum(course_percentages) / len(course_percentages) if course_percentages else 0
			)
			# missing-as-zero has no direct course equivalent: scale down by attendance
			if missing_terms and opts.missing_term_policy == MISSING_TERM_ZERO and expected_terms:
				year_average = year_average * len(term_averages) / len(expected_terms)
		else:
			if opts.missing_term_policy == MISSING_TERM_ZERO and expected_terms:
				year_average = sum(term_averages) / len(expected_terms)
			else:
				year_average = sum(term_averages) / len(term_averages) if term_averages else 0

		doc.year_average = year_average
		doc.terms_expected = len(expected_terms)
		doc.terms_included = len(term_averages)
		doc.is_partial = cint(bool(missing_terms))
		doc.missing_term_policy = opts.missing_term_policy
		doc.year_average_method = opts.year_average_method
		doc.calculation_remarks = (
			_("Missing term(s): {0}").format(", ".join(missing_terms)) if missing_terms else ""
		)

		doc.flags.from_calculation_tool = True
		doc.save(ignore_permissions=True)
		return doc, action

	# -- shared write helpers -----------------------------------------------

	def get_report_shell(self, doctype, filters):
		"""Return (doc, action) where doc is a new or reusable draft document.

		Handles existing reports according to the configured policy:
		draft -> update in place; submitted -> replace (cancel + delete + new)
		or skip, depending on the policy.
		"""
		existing = frappe.get_all(
			doctype, filters=dict(filters, docstatus=["<", 2]), fields=["name", "docstatus"], limit=1
		)
		if not existing:
			return frappe.new_doc(doctype), "created"

		record = existing[0]
		if record.docstatus == 0:
			return frappe.get_doc(doctype, record.name), "updated"

		# submitted
		if self.opts.existing_report_policy == EXISTING_SKIP:
			return None, "skipped_existing"

		old = frappe.get_doc(doctype, record.name)
		old.flags.skip_rank_queue = True
		old.cancel()
		frappe.delete_doc(doctype, record.name, ignore_permissions=True)
		return frappe.new_doc(doctype), "replaced"

	def submit_reports(self, doctype, names, group_name):
		for name in names:
			try:
				doc = frappe.get_doc(doctype, name)
				if doc.docstatus != 0:
					continue
				doc.flags.skip_rank_queue = True
				doc.flags.from_calculation_tool = True
				doc.submit()
				self.counters.submitted += 1
			except Exception:
				self.counters.failed += 1
				self.add_entry(
					"Error",
					_("Could not submit {0}: {1}").format(name, traceback.format_exc()[-500:]),
					student_group=group_name,
				)


def _apply_ranks(doctype, filters, average_field):
	"""Standard-competition ranking (1, 2, 2, 4) over all non-cancelled reports."""
	reports = frappe.get_all(
		doctype, filters=filters, fields=["name", average_field], order_by=f"{average_field} desc"
	)
	prev_average = None
	current_rank = 0
	for i, report in enumerate(reports):
		average = flt(report.get(average_field))
		if prev_average is None or average < prev_average:
			current_rank = i + 1
		prev_average = average
		frappe.db.set_value(doctype, report.name, "rank_in_group", current_rank, update_modified=False)
