# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import calendar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate

from education.education.utils import OverlapError

DAY_MAP = {
	"Monday": "monday",
	"Tuesday": "tuesday",
	"Wednesday": "wednesday",
	"Thursday": "thursday",
	"Friday": "friday",
	"Saturday": "saturday",
	"Sunday": "sunday",
}


class WeeklyCourseScheduleTool(Document):
	@frappe.whitelist()
	def populate_periods(self):
		"""Fetch Period Time Block records for the program and populate the child table."""
		if not self.program:
			frappe.throw(_("Program is required to populate periods."))

		periods = frappe.get_all(
			"Period Time Block",
			filters={"program": self.program},
			fields=["period_number", "period_label", "from_time", "to_time"],
			order_by="period_number asc",
		)

		if not periods:
			frappe.throw(
				_("No Period Time Blocks found for Program {0}. Please create them first.").format(
					self.program
				)
			)

		self.schedule = []
		for p in periods:
			self.append(
				"schedule",
				{
					"period_number": p.period_number,
					"period_label": p.period_label,
					"from_time": p.from_time,
					"to_time": p.to_time,
				},
			)

		return periods

	@frappe.whitelist()
	def get_default_room(self):
		"""Return the Room whose room_name matches the Student Group name."""
		if not self.student_group:
			return None

		room = frappe.db.get_value(
			"Room", {"room_name": self.student_group}, "name"
		)
		return room

	@frappe.whitelist()
	def get_instructor_for_subject(self, course):
		"""Look up the instructor assigned to a given subject for the current student group.

		Checks the Student Group Instructor child table for a row where
		custom_subject matches the given course.
		"""
		if not self.student_group or not course:
			return None

		instructor = frappe.db.get_value(
			"Student Group Instructor",
			{"parent": self.student_group, "custom_subject": course},
			"instructor",
		)
		return instructor

	@frappe.whitelist()
	def create_schedules(self):
		"""Create Course Schedule records based on the weekly period schedule and date range."""
		self.validate_mandatory()
		self.validate_dates()

		created = []
		errors = []
		rescheduled = []
		reschedule_errors = []

		if self.reschedule:
			rescheduled, reschedule_errors = self.delete_existing_schedules()

		date = getdate(self.schedule_start_date)
		end_date = getdate(self.schedule_end_date)

		while date <= end_date:
			day_name = calendar.day_name[date.weekday()]
			day_field = DAY_MAP.get(day_name)

			if not day_field:
				date = add_days(date, 1)
				continue

			for row in self.schedule:
				course = row.get(day_field)
				if not course:
					continue

				instructor_field = day_field + "_instructor"
				instructor = row.get(instructor_field)

				if not instructor:
					instructor = self.get_instructor_for_subject(course)

				if not instructor:
					errors.append(
						{
							"date": str(date),
							"period": row.period_number,
							"course": course,
							"message": _("No instructor found for subject {0}").format(course),
						}
					)
					continue

				try:
					cs = self.make_course_schedule(date, row, course, instructor)
					cs.save()
					created.append(
						{
							"name": cs.name,
							"schedule_date": str(date),
							"course": course,
							"period": row.period_number,
						}
					)
				except OverlapError as e:
					errors.append(
						{
							"date": str(date),
							"period": row.period_number,
							"course": course,
							"message": str(e),
						}
					)

			date = add_days(date, 1)

		return {
			"created": created,
			"errors": errors,
			"rescheduled": rescheduled,
			"reschedule_errors": reschedule_errors,
		}

	def validate_mandatory(self):
		required = ["student_group", "schedule_start_date", "schedule_end_date", "default_room"]
		for field in required:
			if not self.get(field):
				frappe.throw(_("{0} is mandatory").format(self.meta.get_label(field)))

		if not self.schedule or len(self.schedule) == 0:
			frappe.throw(_("Please populate the period schedule first."))

		has_any_subject = False
		for row in self.schedule:
			for day_field in DAY_MAP.values():
				if row.get(day_field):
					has_any_subject = True
					break
			if has_any_subject:
				break

		if not has_any_subject:
			frappe.throw(_("Please assign at least one subject to a period."))

	def validate_dates(self):
		if getdate(self.schedule_start_date) > getdate(self.schedule_end_date):
			frappe.throw(_("Schedule Start Date cannot be greater than Schedule End Date."))

	def delete_existing_schedules(self):
		rescheduled = []
		reschedule_errors = []

		schedules = frappe.get_all(
			"Course Schedule",
			filters={
				"student_group": self.student_group,
				"schedule_date": ["between", [self.schedule_start_date, self.schedule_end_date]],
			},
			fields=["name"],
		)

		for d in schedules:
			try:
				frappe.delete_doc("Course Schedule", d.name)
				rescheduled.append(d.name)
			except Exception:
				reschedule_errors.append(d.name)

		return rescheduled, reschedule_errors

	def make_course_schedule(self, date, row, course, instructor):
		instructor_name = frappe.db.get_value("Instructor", instructor, "instructor_name")

		cs = frappe.new_doc("Course Schedule")
		cs.student_group = self.student_group
		cs.course = course
		cs.instructor = instructor
		cs.instructor_name = instructor_name
		cs.room = self.default_room
		cs.schedule_date = date
		cs.from_time = row.from_time
		cs.to_time = row.to_time
		cs.class_schedule_color = self.class_schedule_color or "blue"
		return cs
