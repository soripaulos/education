# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, nowtime, getdate


@frappe.whitelist()
def get_student_group_current_instructor(student_group):
	"""Return the instructor currently teaching the given student group (by current date/time)."""
	today = nowdate()
	now = nowtime()

	schedules = frappe.db.sql(
		"""
		SELECT
			cs.name, cs.course, cs.instructor, cs.instructor_name,
			cs.from_time, cs.to_time, cs.room, cs.class_schedule_color
		FROM `tabCourse Schedule` cs
		WHERE cs.student_group = %s
			AND cs.schedule_date = %s
			AND cs.from_time <= %s
			AND cs.to_time >= %s
		ORDER BY cs.from_time
		""",
		(student_group, today, now, now),
		as_dict=True,
	)
	return schedules


@frappe.whitelist()
def get_instructor_daily_schedule(instructor, date=None):
	"""Return all course schedules for an instructor on a given date."""
	if not date:
		date = nowdate()

	now = nowtime()
	today = nowdate()

	schedules = frappe.db.sql(
		"""
		SELECT
			cs.name, cs.course, cs.student_group, cs.instructor_name,
			cs.from_time, cs.to_time, cs.room, cs.schedule_date,
			cs.class_schedule_color, cs.program
		FROM `tabCourse Schedule` cs
		WHERE cs.instructor = %s
			AND cs.schedule_date = %s
		ORDER BY cs.from_time
		""",
		(instructor, date),
		as_dict=True,
	)

	is_today = getdate(date) == getdate(today)
	for s in schedules:
		s["is_ongoing"] = False
		if is_today and s["from_time"] and s["to_time"]:
			from_t = str(s["from_time"])
			to_t = str(s["to_time"])
			if from_t <= now <= to_t:
				s["is_ongoing"] = True

	return schedules


@frappe.whitelist()
def get_student_group_timetable(student_group, date=None):
	"""Return the period-based timetable for a student group on a given date."""
	if not date:
		date = nowdate()

	program = frappe.db.get_value("Student Group", student_group, "program")
	if not program:
		return {"periods": [], "schedules": []}

	periods = frappe.get_all(
		"Period Time Block",
		filters={"program": program},
		fields=["period_number", "period_label", "from_time", "to_time"],
		order_by="period_number asc",
	)

	schedules = frappe.db.sql(
		"""
		SELECT
			cs.name, cs.course, cs.instructor, cs.instructor_name,
			cs.from_time, cs.to_time, cs.room, cs.class_schedule_color
		FROM `tabCourse Schedule` cs
		WHERE cs.student_group = %s
			AND cs.schedule_date = %s
		ORDER BY cs.from_time
		""",
		(student_group, date),
		as_dict=True,
	)

	now = nowtime()
	today = nowdate()
	is_today = getdate(date) == getdate(today)

	period_data = []
	for p in periods:
		matched = None
		for s in schedules:
			if str(s["from_time"]) == str(p["from_time"]) and str(s["to_time"]) == str(p["to_time"]):
				matched = s
				break

		is_ongoing = False
		if is_today and p["from_time"] and p["to_time"]:
			from_t = str(p["from_time"])
			to_t = str(p["to_time"])
			if from_t <= now <= to_t:
				is_ongoing = True

		period_data.append(
			{
				"period_number": p["period_number"],
				"period_label": p["period_label"],
				"from_time": str(p["from_time"]),
				"to_time": str(p["to_time"]),
				"course": matched["course"] if matched else None,
				"instructor": matched["instructor"] if matched else None,
				"instructor_name": matched["instructor_name"] if matched else None,
				"room": matched["room"] if matched else None,
				"schedule_name": matched["name"] if matched else None,
				"color": matched["class_schedule_color"] if matched else None,
				"is_ongoing": is_ongoing,
			}
		)

	return {
		"periods": period_data,
		"program": program,
		"date": date,
	}
