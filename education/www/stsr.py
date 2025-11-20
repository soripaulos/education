import frappe
from frappe import _

from education.api import stsr as stsr_api


def get_context(context):
    context.no_cache = 1
    context.title = _("STSR Score Entry")
    context.default_academic_year = stsr_api.DEFAULT_ACADEMIC_YEAR
    context.semester_options = stsr_api.SEMESTER_OPTIONS
    context.exam_options = stsr_api.EXAM_OPTIONS
    context.exam_max_scores = stsr_api.EXAM_MAX_SCORES
    context.show_sidebar = False
    return context
