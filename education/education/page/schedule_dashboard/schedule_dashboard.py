# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime, nowdate


def _fmt_time(t):
	"""Convert a DB TIME value (timedelta or string) to a consistent HH:MM:SS string."""
	if t is None:
		return ""
	from frappe.utils import get_time

	t_obj = get_time(t)
	if t_obj:
		return t_obj.strftime("%H:%M:%S")
	return str(t) if t else ""


def _is_ongoing(from_time, to_time):
	"""Return True if the current server time falls within [from_time, to_time]."""
	if not from_time or not to_time:
		return False
	from frappe.utils import get_time

	now_t = now_datetime().time()
	try:
		from_t = get_time(from_time)
		to_t = get_time(to_time)
		return from_t <= now_t <= to_t
	except Exception:
		return False


@frappe.whitelist()
def get_student_group_current_instructor(student_group):
	"""Return classes currently in session for a student group (today, current time)."""
	today = nowdate()
	now = now_datetime().strftime("%H:%M:%S")

	rows = frappe.db.sql(
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

	for r in rows:
		r["from_time"] = _fmt_time(r["from_time"])
		r["to_time"] = _fmt_time(r["to_time"])

	return rows


@frappe.whitelist()
def get_instructor_daily_schedule(instructor, date=None):
	"""Return all Course Schedules for an instructor on a given date."""
	if not date:
		date = nowdate()

	rows = frappe.db.sql(
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

	is_today = getdate(date) == getdate(nowdate())

	for r in rows:
		from_raw = r["from_time"]
		to_raw = r["to_time"]
		r["from_time"] = _fmt_time(from_raw)
		r["to_time"] = _fmt_time(to_raw)
		r["is_ongoing"] = is_today and _is_ongoing(from_raw, to_raw)

	return rows


@frappe.whitelist()
def get_student_group_timetable(student_group, start_date=None, end_date=None, date=None):
	"""Return period-by-period timetable for a student group over a date range.

	Accepts either a single ``date`` (backward-compat) or a ``start_date``/
	``end_date`` range.  Dates that have no Course Schedule records are omitted
	from the results so the UI never renders an empty table.
	"""
	from datetime import timedelta

	# Backward-compat: single date via old parameter name
	if date and not start_date:
		start_date = date
	if not start_date:
		start_date = nowdate()
	if not end_date:
		end_date = start_date

	program = frappe.db.get_value("Student Group", student_group, "program")
	if not program:
		return {"results": [], "program": None}

	periods = frappe.get_all(
		"Period Time Block",
		filters={"program": program},
		fields=["period_number", "period_label", "from_time", "to_time"],
		order_by="period_number asc",
	)

	if not periods:
		return {"results": [], "program": program}

	# Pre-format period times once so inner-loop comparisons are cheap
	for p in periods:
		p["from_time_fmt"] = _fmt_time(p["from_time"])
		p["to_time_fmt"] = _fmt_time(p["to_time"])

	start_dt = getdate(start_date)
	end_dt = getdate(end_date)
	today = getdate(nowdate())

	_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

	results = []
	current = start_dt

	while current <= end_dt:
		current_str = str(current)

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
			(student_group, current_str),
			as_dict=True,
		)

		# Skip dates that have no scheduled classes
		if schedules:
			is_today = current == today

			# Build a lookup keyed by the schedule's from_time (HH:MM:SS).
			# Matching by from_time alone is more robust than requiring an exact
			# from_time AND to_time match, in case time values differ slightly.
			sched_by_from = {}
			for s in schedules:
				ft = _fmt_time(s["from_time"])
				if ft not in sched_by_from:
					sched_by_from[ft] = s

			period_data = []
			for p in periods:
				matched = sched_by_from.get(p["from_time_fmt"])
				period_data.append(
					{
						"period_number": p["period_number"],
						"period_label": p["period_label"],
						"from_time": p["from_time_fmt"],
						"to_time": p["to_time_fmt"],
						"course": matched["course"] if matched else None,
						"instructor": matched["instructor"] if matched else None,
						"instructor_name": matched["instructor_name"] if matched else None,
						"room": matched["room"] if matched else None,
						"schedule_name": matched["name"] if matched else None,
						"color": matched["class_schedule_color"] if matched else None,
						"is_ongoing": is_today and _is_ongoing(p["from_time"], p["to_time"]),
					}
				)

			results.append(
				{
					"date": current_str,
					"day_of_week": _DAY_NAMES[current.weekday()],
					"periods": period_data,
				}
			)

		current = current + timedelta(days=1)

	return {"results": results, "program": program}


@frappe.whitelist()
def get_instructors_query(doctype, txt, searchfield, start, page_len, filters=None):
	"""Search query for Instructor link field filtered to instructors scheduled on a given date."""
	import json

	if isinstance(filters, str):
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}

	filters = filters or {}
	date = filters.get("date") or nowdate()
	txt = f"%{txt or ''}%"

	return frappe.db.sql(
		"""
		SELECT i.name, i.instructor_name
		FROM `tabInstructor` i
		WHERE i.name IN (
			SELECT DISTINCT cs.instructor
			FROM `tabCourse Schedule` cs
			WHERE cs.schedule_date = %(date)s
		)
		AND (i.name LIKE %(txt)s OR i.instructor_name LIKE %(txt)s)
		ORDER BY i.instructor_name
		LIMIT %(start)s, %(page_len)s
		""",
		{
			"date": date,
			"txt": txt,
			"start": cint(start),
			"page_len": cint(page_len),
		},
	)
