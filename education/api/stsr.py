import frappe
from frappe import _
from frappe.utils import flt, cstr

DEFAULT_ACADEMIC_YEAR = "2018 E.C."
SEMESTER_OPTIONS = [
    "2018 E.C. (First Semester)",
    "2018 E.C. (Second Semester)",
]

EXAM_OPTIONS = [
    {"label": _("First Test (15 marks)"), "value": "First Test", "max_score": 15},
    {"label": _("Second Test (15 marks)"), "value": "Second Test", "max_score": 15},
    {"label": _("Mid Exam (20 marks)"), "value": "Mid Exam", "max_score": 20},
    {"label": _("Final Exam (50 marks)"), "value": "Final Exam", "max_score": 50},
]

EXAM_MAX_SCORES = {exam["value"]: exam["max_score"] for exam in EXAM_OPTIONS}


def _require_login():
    if frappe.session.user == "Guest":
        frappe.throw(_("You must be logged in to access the roster page."), frappe.PermissionError)


def _get_exam_maximum(exam):
    if exam not in EXAM_MAX_SCORES:
        frappe.throw(_("Unsupported exam type: {0}").format(frappe.bold(exam)))
    return EXAM_MAX_SCORES[exam]


@frappe.whitelist()
def get_student_groups():
    """Return active student groups visible to the user."""
    _require_login()

    groups = frappe.db.get_list(
        "Student Group",
        filters={"disabled": 0},
        fields=[
            "name",
            "student_group_name",
            "program",
            "academic_year",
            "group_based_on",
        ],
        order_by="student_group_name asc",
        limit_page_length=500,
    )
    return groups


@frappe.whitelist()
def get_student_group_students(student_group):
    """Fetch group metadata and its active students."""
    _require_login()

    if not student_group:
        frappe.throw(_("Student Group is required"))

    group = frappe.db.get_value(
        "Student Group",
        student_group,
        [
            "name",
            "student_group_name",
            "program",
            "academic_year",
            "batch",
            "course",
        ],
        as_dict=True,
    )

    if not group:
        frappe.throw(_("Student Group {0} not found").format(frappe.bold(student_group)))

    students = frappe.db.get_all(
        "Student Group Student",
        filters={
            "parent": student_group,
            "parenttype": "Student Group",
            "active": 1,
        },
        fields=["student", "student_name", "group_roll_number"],
        order_by="idx asc",
        limit_page_length=1000,
    )

    return {"group": group, "students": students}


@frappe.whitelist()
def get_program_subjects(program):
    """Return subjects (courses) configured for a program."""
    _require_login()

    if not program:
        frappe.throw(_("Program is required to load subjects"))

    courses = frappe.db.get_all(
        "Program Course",
        filters={
            "parent": program,
            "parenttype": "Program",
        },
        fields=["course as name", "course_name"],
        order_by="idx asc",
        limit_page_length=500,
    )

    return courses


@frappe.whitelist()
def get_existing_scores(
    academic_year: str,
    semester: str,
    subject: str,
    student_group: str,
    exam: str,
):
    """Fetch draft and submitted Student Term Subject Result rows for the selection."""
    _require_login()

    if not all([academic_year, semester, subject, student_group, exam]):
        frappe.throw(_("Academic Year, Semester, Subject, Student Group, and Exam are required"))

    results = frappe.db.get_list(
        "Student Term Subject Result",
        filters={
            "academic_year": academic_year,
            "semester": semester,
            "subject": subject,
            "student_group": student_group,
            "exam": exam,
        },
        fields=[
            "name",
            "student",
            "student_name",
            "score",
            "max_score",
            "grade",
            "docstatus",
        ],
        order_by="student_name asc",
        limit_page_length=2000,
    )

    return results


def _validate_entry(entry):
    required = [
        "student",
        "student_name",
        "student_group",
        "subject",
        "exam",
        "academic_year",
        "semester",
        "grade",
    ]

    missing = [field for field in required if not entry.get(field)]
    if missing:
        frappe.throw(_("Missing values for {0}").format(", ".join(missing)))

    exam = entry.get("exam")
    max_score = _get_exam_maximum(exam)
    score = flt(entry.get("score"))

    if score < 0 or score > max_score:
        frappe.throw(
            _("Score for {0} must be between 0 and {1}").format(exam, max_score)
        )

    entry["max_score"] = max_score
    entry["score"] = score
    return entry


def _create_or_update_score(entry):
    entry = _validate_entry(entry)
    existing_name = entry.get("name")

    if existing_name:
        existing_doc = frappe.get_doc("Student Term Subject Result", existing_name)
    else:
        existing_doc = None

    if existing_doc and existing_doc.docstatus == 0:
        existing_doc.update(
            {
                "student": entry["student"],
                "student_name": entry["student_name"],
                "academic_year": entry["academic_year"],
                "semester": entry["semester"],
                "subject": entry["subject"],
                "student_group": entry["student_group"],
                "grade": entry["grade"],
                "exam": entry["exam"],
                "score": entry["score"],
                "max_score": entry["max_score"],
            }
        )
        existing_doc.save(ignore_permissions=True)
        if existing_doc.docstatus == 0:
            existing_doc.submit()
        return existing_doc

    if existing_doc and existing_doc.docstatus == 1:
        existing_doc.cancel()
        amended_from = existing_doc.name
    else:
        amended_from = None

    doc = frappe.new_doc("Student Term Subject Result")
    doc.update(
        {
            "student": entry["student"],
            "student_name": entry["student_name"],
            "academic_year": entry["academic_year"],
            "semester": entry["semester"],
            "subject": entry["subject"],
            "student_group": entry["student_group"],
            "grade": entry["grade"],
            "exam": entry["exam"],
            "score": entry["score"],
            "max_score": entry["max_score"],
        }
    )

    if amended_from:
        doc.amended_from = amended_from

    doc.insert(ignore_permissions=True)
    doc.submit()
    return doc


@frappe.whitelist()
def save_scores_batch(entries):
    """Create or update Student Term Subject Result rows and submit them."""
    _require_login()
    parsed_entries = frappe.parse_json(entries) if isinstance(entries, str) else entries

    if not parsed_entries:
        frappe.throw(_("No scores were provided to save"))

    saved = []
    errors = []

    for entry in parsed_entries:
        try:
            doc = _create_or_update_score(entry)
            saved.append(
                {
                    "name": doc.name,
                    "student": doc.student,
                    "exam": doc.exam,
                    "score": doc.score,
                    "max_score": doc.max_score,
                    "docstatus": doc.docstatus,
                }
            )
        except Exception as exc:
            frappe.log_error(
                title="Roster score save failure",
                message=f"Entry: {entry}\nError: {frappe.get_traceback()}",
            )
            error_message = getattr(exc, "message", None) or cstr(exc)
            errors.append({"entry": entry, "error": error_message})

    return {"saved": saved, "errors": errors}


@frappe.whitelist()
def delete_scores(docnames=None, filters=None):
    """Delete Student Term Subject Result rows for the provided docnames or filters."""
    _require_login()

    docnames = frappe.parse_json(docnames) if isinstance(docnames, str) else docnames
    filters = frappe.parse_json(filters) if isinstance(filters, str) else filters

    if not docnames:
        if not filters:
            frappe.throw(_("Provide docnames or filters to delete scores"))
        docnames = frappe.db.get_all(
            "Student Term Subject Result",
            filters=filters,
            pluck="name",
        )

    deleted = []
    for name in docnames:
        doc = frappe.get_doc("Student Term Subject Result", name)
        if doc.docstatus == 1:
            doc.cancel()
        doc.delete(ignore_permissions=True)
        deleted.append(name)

    return {"deleted": deleted}


__all__ = [
    "DEFAULT_ACADEMIC_YEAR",
    "SEMESTER_OPTIONS",
    "EXAM_OPTIONS",
    "EXAM_MAX_SCORES",
    "get_student_groups",
    "get_student_group_students",
    "get_program_subjects",
    "get_existing_scores",
    "save_scores_batch",
    "delete_scores",
]
