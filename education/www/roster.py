import frappe
from frappe import _

from education.api import roster as roster_api


def get_context(context):
    context.no_cache = 1
    context.title = _("Roster Score Entry")
    context.default_academic_year = roster_api.DEFAULT_ACADEMIC_YEAR
    context.semester_options = roster_api.SEMESTER_OPTIONS
    context.exam_options = roster_api.EXAM_OPTIONS
    context.exam_max_scores = roster_api.EXAM_MAX_SCORES
    context.show_sidebar = False
    return context
