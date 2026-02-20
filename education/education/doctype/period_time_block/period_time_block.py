# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PeriodTimeBlock(Document):
	def validate(self):
		self.validate_time()
		self.validate_duplicate()
		if not self.period_label:
			self.period_label = _("Period {0}").format(self.period_number)

	def validate_time(self):
		if self.from_time and self.to_time and self.from_time >= self.to_time:
			frappe.throw(_("From Time cannot be greater than or equal to To Time."))

	def validate_duplicate(self):
		existing = frappe.db.exists(
			"Period Time Block",
			{
				"program": self.program,
				"period_number": self.period_number,
				"name": ("!=", self.name),
			},
		)
		if existing:
			frappe.throw(
				_("Period {0} already exists for Program {1}").format(
					self.period_number, self.program
				)
			)
