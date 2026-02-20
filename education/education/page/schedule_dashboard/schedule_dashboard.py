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
def get_student_group_timetable(student_group, date=None):
	"""Return period-by-period timetable for a student group on a given date."""
	if not date:
		date = nowdate()

	program = frappe.db.get_value("Student Group", student_group, "program")
	if not program:
		return {"periods": [], "program": None, "date": date}

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

	is_today = getdate(date) == getdate(nowdate())

	period_data = []
	for p in periods:
		p_from = _fmt_time(p["from_time"])
		p_to = _fmt_time(p["to_time"])

		matched = None
		for s in schedules:
			if _fmt_time(s["from_time"]) == p_from and _fmt_time(s["to_time"]) == p_to:
				matched = s
				break

		period_data.append(
			{
				"period_number": p["period_number"],
				"period_label": p["period_label"],
				"from_time": p_from,
				"to_time": p_to,
				"course": matched["course"] if matched else None,
				"instructor": matched["instructor"] if matched else None,
				"instructor_name": matched["instructor_name"] if matched else None,
				"room": matched["room"] if matched else None,
				"schedule_name": matched["name"] if matched else None,
				"color": matched["class_schedule_color"] if matched else None,
				"is_ongoing": is_today and _is_ongoing(p["from_time"], p["to_time"]),
			}
		)

	return {
		"periods": period_data,
		"program": program,
		"date": date,
	}


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
