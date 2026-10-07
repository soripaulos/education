"""Who passes the year, according to the school's Promotion Rules.

Each Promotion Rule decides one or more grades (Programs), in one of two ways:

* School Results - the student's Student Year Report: not promoted when the
  year average is below a mark, or when N or more subjects score below a
  mark (any number of such conditions, e.g. 3 below 50 or 2 below 40).
* External Exam - the result written on the student's External Exam Result
  (the Grade 6 / Grade 8 regional exam). Pass or Fail is taken as written.

A rule with no Programs is the default for every grade without its own rule.
With no rule at all, the Promotion Pass Mark in Education Settings applies to
the year average.

The Not Promoted Student list stays the decision that registration and the
enrollment tool act on; these rules suggest who belongs on it.
"""

import frappe
from frappe import _
from frappe.utils import flt

from education.education.lifecycle.common import promotion_failures

PROMOTED = "Promoted"
NOT_PROMOTED = "Not Promoted"
PENDING = "Pending"

SCHOOL_RESULTS = "School Results"
EXTERNAL_EXAM = "External Exam"


def _rules_ready():
	return frappe.db.table_exists("Promotion Rule")


def load_rules():
	"""Enabled rules as (rule_by_program, default_rule)."""
	by_program, default = {}, None
	if not _rules_ready():
		return by_program, default
	for name in frappe.get_all("Promotion Rule", filters={"enabled": 1}, pluck="name", order_by="modified asc"):
		rule = frappe.get_cached_doc("Promotion Rule", name)
		programs = [row.program for row in rule.programs if row.program]
		if not programs:
			default = rule
		for program in programs:
			by_program[program] = rule
	return by_program, default


class Evaluator:
	"""Decides promotion for many students of one academic year, efficiently."""

	def __init__(self, academic_year):
		from education.education.lifecycle.setup import get_setting

		self.academic_year = academic_year
		self.rules_by_program, self.default_rule = load_rules()
		self.fallback_mark = flt(get_setting("promotion_pass_mark")) or 60.0
		self._reports = None
		self._exams = None

	# -- data, loaded on first use ------------------------------------------
	def _load_reports(self):
		self._reports = {}
		reports = frappe.get_all(
			"Student Year Report",
			filters={"academic_year": self.academic_year},
			fields=["name", "student", "year_average"],
			order_by="modified asc",
			limit_page_length=0,
		)
		for row in reports:
			# The latest report wins if a student somehow has two.
			self._reports[row.student] = frappe._dict(name=row.name, average=row.year_average, subjects={})
		by_name = {r.name: r for r in self._reports.values()}
		if by_name:
			for row in frappe.get_all(
				"Course Year Summary",
				filters={"parenttype": "Student Year Report", "parent": ["in", list(by_name)]},
				fields=["parent", "course", "year_average_percentage", "excluded_from_average"],
				limit_page_length=0,
			):
				report = by_name.get(row.parent)
				if report and not row.excluded_from_average and row.course:
					report.subjects[row.course] = row.year_average_percentage
		for report in self._reports.values():
			if not flt(report.average) and report.subjects:
				values = [flt(v) for v in report.subjects.values() if v is not None]
				report.average = sum(values) / len(values) if values else None

	def _load_exams(self):
		self._exams = {}
		if not frappe.db.table_exists("External Exam Result"):
			return
		for row in frappe.get_all(
			"External Exam Result",
			filters={"academic_year": self.academic_year, "docstatus": 1},
			fields=["name", "student", "exam_type", "result_status", "average_percentage"],
			limit_page_length=0,
		):
			self._exams[(row.student, row.exam_type)] = row

	def report(self, student):
		if self._reports is None:
			self._load_reports()
		return self._reports.get(student)

	def exam(self, student, exam_type):
		if self._exams is None:
			self._load_exams()
		return self._exams.get((student, exam_type))

	# -- decisions ----------------------------------------------------------
	def rule_for(self, program):
		return self.rules_by_program.get(program) or self.default_rule

	def evaluate(self, student, program):
		"""Decision for one student in ``program`` during this academic year.

		Returns a dict: decision (Promoted / Not Promoted / Pending), reasons
		(list), rule (name or ""), average.
		"""
		rule = self.rule_for(program)
		result = frappe._dict(decision=PENDING, reasons=[], rule=rule.name if rule else "", average=None)

		if rule and rule.decided_by == EXTERNAL_EXAM:
			exam = self.exam(student, rule.exam_type)
			if not exam:
				result.reasons.append(_("No submitted {0} result").format(rule.exam_type))
			elif exam.result_status == "Pass":
				result.decision = PROMOTED
				result.average = exam.average_percentage
			elif exam.result_status == "Fail":
				result.decision = NOT_PROMOTED
				result.average = exam.average_percentage
				result.reasons.append(_("Failed the {0} ({1})").format(rule.exam_type, exam.name))
			else:
				result.reasons.append(
					_("{0} result is {1}").format(rule.exam_type, exam.result_status or _("Pending"))
				)
			return result

		report = self.report(student)
		if not report:
			result.reasons.append(_("No Student Year Report for {0}").format(self.academic_year))
			return result
		result.average = report.average

		if rule:
			conditions = [(c.failed_subjects, c.subject_mark_below) for c in rule.conditions]
			reasons = promotion_failures(report.average, report.subjects, rule.year_average_below, conditions)
		else:
			reasons = promotion_failures(report.average, report.subjects, self.fallback_mark, [])
		result.reasons = reasons
		result.decision = NOT_PROMOTED if reasons else PROMOTED
		return result


def evaluate(student, academic_year, program):
	"""One-off decision; use :class:`Evaluator` for many students."""
	return Evaluator(academic_year).evaluate(student, program)


# ---------------------------------------------------------------------------
# Not Promoted list, suggested from the rules
# ---------------------------------------------------------------------------


def _check_staff():
	frappe.only_for(("System Manager", "Education Manager", "Academics User"))


@frappe.whitelist()
def get_not_promoted_suggestions(academic_year):
	"""Students enrolled in ``academic_year`` whom the rules do not promote and
	who are not on that year's Not Promoted list yet."""
	_check_staff()
	evaluator = Evaluator(academic_year)
	listed = set(
		frappe.get_all("Not Promoted Student", filters={"academic_year": academic_year}, pluck="student")
	)
	enrollments = frappe.db.sql(
		"""
		SELECT pe.student, pe.program, s.student_name, s.custom_school_id
		FROM `tabProgram Enrollment` pe
		JOIN `tabStudent` s ON s.name = pe.student
		WHERE pe.academic_year = %s AND pe.docstatus = 1 AND s.enabled = 1
		ORDER BY pe.program, s.student_name
		""",
		(academic_year,),
		as_dict=True,
	)
	suggestions, pending = [], 0
	for row in enrollments:
		if row.student in listed:
			continue
		result = evaluator.evaluate(row.student, row.program)
		if result.decision == PENDING:
			pending += 1
		if result.decision != NOT_PROMOTED:
			continue
		suggestions.append(
			{
				"student": row.student,
				"student_name": row.student_name,
				"school_id": row.custom_school_id,
				"program": row.program,
				"average": result.average,
				"rule": result.rule,
				"reasons": "; ".join(result.reasons),
			}
		)
	return {"suggestions": suggestions, "pending": pending, "checked": len(enrollments)}


@frappe.whitelist()
def create_not_promoted_records(academic_year, students):
	"""Add the given students to ``academic_year``'s Not Promoted list."""
	_check_staff()
	students = frappe.parse_json(students) if isinstance(students, str) else students
	wanted = set(students or [])
	created = []
	for row in get_not_promoted_suggestions(academic_year)["suggestions"]:
		if row["student"] not in wanted:
			continue
		doc = frappe.new_doc("Not Promoted Student")
		doc.school_id = row["school_id"] or row["student"]
		doc.student = row["student"]
		doc.student_name = row["student_name"]
		doc.academic_year = academic_year
		doc.current_program = row["program"]
		doc.reason = _("Promotion rule {0}: {1}").format(row["rule"] or _("(pass mark)"), row["reasons"])
		doc.insert()
		created.append(doc.name)
	return created
