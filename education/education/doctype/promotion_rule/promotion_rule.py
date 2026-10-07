# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A promotion rule for one or more grades. See ``lifecycle.promotion``."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from education.education.lifecycle.common import describe_condition


class PromotionRule(Document):
	def validate(self):
		self.validate_criteria()
		self.validate_programs()
		self.set_summary()

	def validate_criteria(self):
		if self.decided_by == "External Exam":
			if not self.exam_type:
				frappe.throw(_("Choose the exam that decides promotion."))
			return
		for row in self.conditions:
			if cint(row.failed_subjects) <= 0 or flt(row.subject_mark_below) <= 0:
				frappe.throw(
					_("Row {0}: give a number of subjects and a mark, both above zero.").format(row.idx)
				)
			row.description = describe_condition(row.failed_subjects, row.subject_mark_below)
		if not flt(self.year_average_below) and not self.conditions:
			frappe.throw(_("Give a year average, at least one failed-subject condition, or both."))

	def validate_programs(self):
		"""A grade is decided by one enabled rule; only one rule may be the default."""
		if not self.enabled:
			return
		mine = [row.program for row in self.programs if row.program]
		if len(mine) != len(set(mine)):
			frappe.throw(_("A program is listed twice."))
		for other in frappe.get_all(
			"Promotion Rule", filters={"enabled": 1, "name": ["!=", self.name]}, pluck="name"
		):
			theirs = frappe.get_all(
				"Promotion Rule Program", filters={"parent": other, "parenttype": "Promotion Rule"}, pluck="program"
			)
			if not mine and not theirs:
				frappe.throw(
					_("{0} is already the default rule (no programs). Disable it or give one of them programs.").format(
						frappe.bold(other)
					)
				)
			clash = sorted(set(mine) & set(theirs))
			if clash:
				frappe.throw(
					_("{0} already decides {1}. A grade can only have one enabled rule.").format(
						frappe.bold(other), ", ".join(clash)
					)
				)

	def set_summary(self):
		if self.decided_by == "External Exam":
			self.summary = _("Pass or Fail as written on the {0} result.").format(self.exam_type)
			return
		parts = []
		if flt(self.year_average_below):
			parts.append(_("year average below {0:g}").format(flt(self.year_average_below)))
		parts += [row.description for row in self.conditions]
		self.summary = _("Not promoted when: {0}").format(_("; or ").join(parts))

	def on_update(self):
		frappe.clear_document_cache("Promotion Rule", self.name)
