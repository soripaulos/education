from __future__ import annotations

from typing import Any, Dict, List, Sequence

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


def _get_exam_maximum(exam: str) -> float:
    if exam not in EXAM_MAX_SCORES:
        frappe.throw(_("Unsupported exam type: {0}").format(frappe.bold(exam)))
    return EXAM_MAX_SCORES[exam]


class STSRService:
    """Service façade for the STSR roster workflow."""

    STUDENT_GROUP_DOCTYPE = "Student Group"
    STUDENT_GROUP_CHILD_DOCTYPE = "Student Group Student"
    PROGRAM_DOCTYPE = "Program"
    PROGRAM_COURSE_CHILD_DOCTYPE = "Program Course"
    RESULT_DOCTYPE = "Student Term Subject Result"

    GROUP_BASE_FIELDS = (
        "name",
        "student_group_name",
        "program",
        "academic_year",
        "batch",
        "course",
    )
    STUDENT_FIELDS = ("student", "student_name", "group_roll_number")
    SCORE_FIELDS = (
        "name",
        "student",
        "student_name",
        "score",
        "max_score",
        "grade",
        "docstatus",
    )

    def __init__(self) -> None:
        self._group_fields: Sequence[str] | None = None
        self._program_fallback_field: str | None = None

    def program_fallback_field(self) -> str | None:
        """Return the first available field that can act as a Program surrogate."""
        if self._program_fallback_field is not None:
            return self._program_fallback_field

        meta = frappe.get_meta(self.STUDENT_GROUP_DOCTYPE)
        for candidate in ("grade", "program_override", "custom_grade"):
            if meta.has_field(candidate):
                self._program_fallback_field = candidate
                break
        else:
            self._program_fallback_field = None
        return self._program_fallback_field

    def group_fields(self) -> Sequence[str]:
        """Base fields plus optional fallbacks, cached for reuse."""
        if self._group_fields is None:
            fields = list(self.GROUP_BASE_FIELDS)
            fallback = self.program_fallback_field()
            if fallback and fallback not in fields:
                fields.append(fallback)
            self._group_fields = tuple(fields)
        return self._group_fields

    def _normalize_group(self, group: Dict[str, Any]) -> Dict[str, Any]:
        fallback_field = self.program_fallback_field()
        program = group.get("program")
        fallback_program = group.get(fallback_field) if fallback_field else None
        resolved_program = program or fallback_program
        if resolved_program:
            group["program"] = resolved_program
        return group

    def list_student_groups(self) -> List[Dict[str, Any]]:
        groups = frappe.db.get_list(
            self.STUDENT_GROUP_DOCTYPE,
            filters={"disabled": 0},
            fields=list(self.group_fields()),
            order_by="student_group_name asc",
            limit_page_length=500,
        )
        return [self._normalize_group(group) for group in groups]

    def fetch_student_group(self, student_group: str) -> Dict[str, Any]:
        group = frappe.db.get_value(
            self.STUDENT_GROUP_DOCTYPE,
            student_group,
            list(self.group_fields()),
            as_dict=True,
        )
        if not group:
            frappe.throw(_("Student Group {0} not found").format(frappe.bold(student_group)))
        return self._normalize_group(group)

    def fetch_group_students(self, student_group: str) -> List[Dict[str, Any]]:
        return frappe.db.get_all(
            self.STUDENT_GROUP_CHILD_DOCTYPE,
            filters={
                "parent": student_group,
                "parenttype": self.STUDENT_GROUP_DOCTYPE,
                "active": 1,
            },
            fields=list(self.STUDENT_FIELDS),
            order_by="idx asc",
            limit_page_length=1000,
        )

    def get_student_group_payload(self, student_group: str) -> Dict[str, Any]:
        group = self.fetch_student_group(student_group)
        students = self.fetch_group_students(student_group)
        return {"group": group, "students": students}

    def get_program_subjects(self, program: str | None) -> List[Dict[str, Any]]:
        if not program:
            return []
        return frappe.db.get_all(
            self.PROGRAM_COURSE_CHILD_DOCTYPE,
            filters={
                "parent": program,
                "parenttype": self.PROGRAM_DOCTYPE,
            },
            fields=["course as name", "course_name"],
            order_by="idx asc",
            limit_page_length=500,
        )

    def get_existing_scores(
        self,
        academic_year: str,
        semester: str,
        subject: str,
        student_group: str,
        exam: str,
    ) -> List[Dict[str, Any]]:
        if not all([academic_year, semester, subject, student_group, exam]):
            frappe.throw(_("Academic Year, Semester, Subject, Student Group, and Exam are required"))

        return frappe.db.get_list(
            self.RESULT_DOCTYPE,
            filters={
                "academic_year": academic_year,
                "semester": semester,
                "subject": subject,
                "student_group": student_group,
                "exam": exam,
            },
            fields=list(self.SCORE_FIELDS),
            order_by="student_name asc",
            limit_page_length=2000,
        )

    def save_scores_batch(self, entries: Any) -> Dict[str, Any]:
        parsed_entries = self._parse_entries(entries)
        if not parsed_entries:
            frappe.throw(_("No scores were provided to save"))

        saved: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for entry in parsed_entries:
            try:
                doc = self._create_or_update_score(entry)
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
            except Exception as exc:  # noqa: BLE001 - propagate summarized errors to UI
                frappe.log_error(
                    title="Roster score save failure",
                    message=f"Entry: {entry}\nError: {frappe.get_traceback()}",
                )
                error_message = getattr(exc, "message", None) or cstr(exc)
                errors.append({"entry": entry, "error": error_message})

        return {"saved": saved, "errors": errors}

    def delete_scores(self, docnames: Any = None, filters: Any = None) -> Dict[str, Any]:
        docnames = self._parse_entries(docnames) if isinstance(docnames, str) else docnames
        filters = frappe.parse_json(filters) if isinstance(filters, str) else filters

        if not docnames:
            if not filters:
                frappe.throw(_("Provide docnames or filters to delete scores"))
            docnames = frappe.db.get_all(
                self.RESULT_DOCTYPE,
                filters=filters,
                pluck="name",
            )

        deleted = []
        for name in docnames:
            doc = frappe.get_doc(self.RESULT_DOCTYPE, name)
            if doc.docstatus == 1:
                doc.cancel()
            doc.delete(ignore_permissions=True)
            deleted.append(name)

        return {"deleted": deleted}

    @staticmethod
    def _parse_entries(entries: Any) -> List[Any]:
        if entries is None:
            return []
        parsed = frappe.parse_json(entries) if isinstance(entries, str) else entries
        if isinstance(parsed, list):
            return list(parsed)
        frappe.throw(_("Entries payload must be a list"))

    def _validate_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
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
            frappe.throw(_("Score for {0} must be between 0 and {1}").format(exam, max_score))

        entry["max_score"] = max_score
        entry["score"] = score
        return entry

    def _create_or_update_score(self, entry: Dict[str, Any]):
        entry = self._validate_entry(entry)
        existing_name = entry.get("name")

        if existing_name:
            existing_doc = frappe.get_doc(self.RESULT_DOCTYPE, existing_name)
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

        doc = frappe.new_doc(self.RESULT_DOCTYPE)
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


service = STSRService()


@frappe.whitelist()
def get_student_groups():
    """Return active student groups visible to the user."""
    _require_login()
    return service.list_student_groups()


@frappe.whitelist()
def get_student_group_students(student_group: str):
    """Fetch group metadata and its active students."""
    _require_login()
    if not student_group:
        frappe.throw(_("Student Group is required"))
    return service.get_student_group_payload(student_group)


@frappe.whitelist()
def get_program_subjects(program: str | None = None):
    """Return subjects (courses) configured for a program."""
    _require_login()
    return service.get_program_subjects(program)


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
    return service.get_existing_scores(academic_year, semester, subject, student_group, exam)


@frappe.whitelist()
def save_scores_batch(entries: Any):
    """Create or update Student Term Subject Result rows and submit them."""
    _require_login()
    return service.save_scores_batch(entries)


@frappe.whitelist()
def delete_scores(docnames: Any = None, filters: Any = None):
    """Delete Student Term Subject Result rows for the provided docnames or filters."""
    _require_login()
    return service.delete_scores(docnames=docnames, filters=filters)


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
