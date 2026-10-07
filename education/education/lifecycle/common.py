"""Pure helpers shared by the lifecycle tools.

Nothing in here touches the database, so the rules about grades, streams,
names and phone numbers can be reasoned about (and tested) on their own.
"""

import re
from difflib import SequenceMatcher

# Every grade the school teaches, in the order a student moves through them.
GRADE_ORDER = ["Nursery", "LKG", "UKG"] + [f"Grade {n}" for n in range(1, 13)]

# Medium / stream suffixes that ride along with a grade: "Grade 4 AO",
# "Grade 11 NS". AO is the Afaan Oromo medium; NS/SS are the Grade 11-12
# natural and social science streams.
PROGRAM_SUFFIXES = ("AO", "NS", "SS")

FINAL_GRADE = "Grade 12"

BRANCHES = ("Main", "MBS #2", "MBS Dembi Dollo")

# Severity of an issue, worst first. A row's status follows its worst issue.
BLOCKED = "Blocked"
REVIEW = "Review"
INFO = "Info"
SEVERITY_RANK = {BLOCKED: 0, REVIEW: 1, INFO: 2}


def clean_spaces(value):
	return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_school_id(value):
	"""Canonical comparison key for a School ID.

	Spreadsheets hand numeric IDs back as floats (``4464.0``) and people type
	IDs in whatever case and spacing they like; none of that should stop
	``m1/13970/18 `` matching ``M1/13970/18``.
	"""
	if value is None:
		return ""
	if isinstance(value, float) and value.is_integer():
		value = int(value)
	text = str(value).strip().upper().replace(" ", "")
	if re.fullmatch(r"\d+\.0", text):
		text = text[:-2]
	return text


def split_program(program):
	"""Split "Grade 8 AO" into ("Grade 8", "AO"); "LKG" into ("LKG", "")."""
	program = clean_spaces(program)
	match = re.search(r"\s+(%s)$" % "|".join(PROGRAM_SUFFIXES), program)
	if match:
		return program[: match.start()].strip(), match.group(1)
	return program, ""


def grade_index(program):
	"""Position of a program's grade in GRADE_ORDER, or None if unknown."""
	base, _suffix = split_program(program)
	try:
		return GRADE_ORDER.index(base)
	except ValueError:
		return None


def grade_of_section(section):
	"""The grade a section's name points at: "Grade 10 A" -> "Grade 10".

	Longest names are tried first so "Grade 12 B" is not read as "Grade 1".
	Spacing is ignored, which also copes with roster spellings like "UKGF".
	"""
	compact = clean_spaces(section).replace(" ", "").lower()
	for grade in sorted(GRADE_ORDER, key=len, reverse=True):
		if compact.startswith(grade.replace(" ", "").lower()):
			return grade
	return None


def is_final_grade(program):
	return split_program(program)[0] == FINAL_GRADE


def next_program(program, existing_programs):
	"""The program a promoted student moves into, or None after Grade 12.

	Mirrors the registration page's rule so both agree: the medium suffix is
	kept where the next grade offers it ("Grade 3 AO" -> "Grade 4 AO") and
	dropped where it does not ("Grade 9 AO" -> "Grade 10"); Grade 11 and 12
	default to the NS stream.
	"""
	base, suffix = split_program(program)
	index = grade_index(base)
	if index is None:
		return program or None
	if GRADE_ORDER[index] == FINAL_GRADE:
		return None

	next_base = GRADE_ORDER[index + 1]
	next_number = re.match(r"^Grade (\d+)$", next_base)
	if next_number and int(next_number.group(1)) >= 11 and not suffix:
		suffix = "NS"

	candidates = [f"{next_base} {suffix}"] if suffix else []
	candidates.append(next_base)
	for candidate in candidates:
		if candidate in existing_programs:
			return candidate
	return candidates[0]


# Movement codes, from the previous year's program to the new one.
NEW = "New"
PROMOTED = "Promoted"
REPEATING = "Repeating"
SKIPPED = "Skipped a grade"
MOVED_DOWN = "Moved down"
UNKNOWN = "Unknown"


def classify_movement(previous_program, new_program, existing_programs=()):
	"""Describe how a student moves between two programs.

	Returns ``(movement, stream_note)``. ``stream_note`` is empty when the
	stream/medium is unchanged or changes the way it always does (the AO
	medium ending after Grade 9, a stream being chosen at Grade 11).
	"""
	if not previous_program:
		return NEW, ""

	prev_index = grade_index(previous_program)
	new_index = grade_index(new_program)
	if prev_index is None or new_index is None:
		return UNKNOWN, ""

	step = new_index - prev_index
	if step == 0:
		movement = REPEATING
	elif step == 1:
		movement = PROMOTED
	elif step > 1:
		movement = SKIPPED
	else:
		movement = MOVED_DOWN

	prev_suffix = split_program(previous_program)[1]
	new_suffix = split_program(new_program)[1]
	stream_note = ""
	if prev_suffix != new_suffix:
		expected = next_program(previous_program, existing_programs) if step == 1 else None
		if not (expected and expected == clean_spaces(new_program)):
			stream_note = "{0} -> {1}".format(prev_suffix or "regular", new_suffix or "regular")
	return movement, stream_note


def normalize_name(name):
	"""Lower-case, punctuation-free, single-spaced version of a full name."""
	name = str(name or "").lower()
	# Apostrophes vanish rather than split a word: Ya'e / Ya’e -> yae.
	name = re.sub(r"[’'`´]", "", name)
	name = re.sub(r"[^\w\s]", " ", name)
	return clean_spaces(name)


SAME = "same"
VARIATION = "variation"
CONFLICT = "conflict"


def compare_names(first, second):
	"""How confident we are that two full names belong to the same person.

	``same``      - identical once case/spacing/punctuation are ignored.
	``variation`` - reordered, a missing or abbreviated part, or a close
	                spelling (transliteration of Afaan Oromo names drifts).
	``conflict``  - looks like a different person.
	"""
	a, b = normalize_name(first), normalize_name(second)
	if not a or not b:
		return VARIATION
	if a == b:
		return SAME

	tokens_a, tokens_b = a.split(), b.split()
	if sorted(tokens_a) == sorted(tokens_b):
		return VARIATION
	shorter, longer = sorted((set(tokens_a), set(tokens_b)), key=len)
	if len(shorter) >= 2 and shorter <= longer:
		return VARIATION

	ratio = SequenceMatcher(None, a, b).ratio()
	if ratio >= 0.85:
		return VARIATION
	first_names_close = SequenceMatcher(None, tokens_a[0], tokens_b[0]).ratio() >= 0.8
	if first_names_close and ratio >= 0.7:
		return VARIATION
	return CONFLICT


def worst_severity(issues):
	"""The most serious severity among ``issues`` (None when there are none)."""
	ranked = sorted((SEVERITY_RANK.get(i["severity"], 9), i["severity"]) for i in issues)
	return ranked[0][1] if ranked else None


def format_issues(issues):
	"""One line per issue, worst first, for the tool's Issues column."""
	ordered = sorted(issues, key=lambda i: SEVERITY_RANK.get(i["severity"], 9))
	return "\n".join("[{0}] {1}".format(i["severity"], i["message"]) for i in ordered)


def branch_of_section(section, explicit=None):
	"""Branch a section serves, from its Branch field or its name.

	Second-branch sections have always carried "Branch" in their name
	("Grade 1 A Branch"); Dembi Dollo sections are prefixed "DD".
	"""
	if explicit:
		return explicit
	name = clean_spaces(section)
	if not name:
		return ""
	if re.search(r"\bbranch\b", name, re.I):
		return "MBS #2"
	if re.match(r"^(dd|dembi)\b", name, re.I):
		return "MBS Dembi Dollo"
	return "Main"


def local_phone_digits(phone):
	"""The nine-digit subscriber number from an Ethiopian mobile number.

	``+251912345678``, ``251912345678``, ``0912345678`` and ``912345678`` all
	give ``912345678``. Anything that does not reduce to nine digits starting
	with 9 (Ethio telecom) or 7 (Safaricom) returns "".
	"""
	digits = re.sub(r"\D", "", str(phone or ""))
	if digits.startswith("251") and len(digits) > 9:
		digits = digits[3:]
	if digits.startswith("0") and len(digits) == 10:
		digits = digits[1:]
	if len(digits) == 9 and digits[0] in "97":
		return digits
	return ""


def phone_password_candidates(phone):
	"""Initial passwords for a student login, in order of preference.

	The school's rule: the family's phone number written locally
	(``0912345678``). When that is rejected by the password policy the
	international form without the plus (``251912345678``) is used instead.
	"""
	local = local_phone_digits(phone)
	if not local:
		return []
	return ["0" + local, "251" + local]
