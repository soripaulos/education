"""Tests for the pure lifecycle rules. They need no site:

    python -m unittest education.education.lifecycle.test_common
"""

import unittest

from education.education.lifecycle import common
from education.education.lifecycle.common import (
	CONFLICT,
	MOVED_DOWN,
	NEW,
	PROMOTED,
	REPEATING,
	SAME,
	SKIPPED,
	VARIATION,
)

PROGRAMS = {
	"Nursery",
	"Nursery AO",
	"LKG",
	"LKG AO",
	"UKG",
	"UKG AO",
	"Grade 10",
	"Grade 11 NS",
	"Grade 12 NS",
	"Grade 12 SS",
} | {f"Grade {n}" for n in range(1, 10)} | {f"Grade {n} AO" for n in range(1, 10)}


class TestPrograms(unittest.TestCase):
	def test_split_program(self):
		self.assertEqual(common.split_program("Grade 8 AO"), ("Grade 8", "AO"))
		self.assertEqual(common.split_program(" Grade  11 NS "), ("Grade 11", "NS"))
		self.assertEqual(common.split_program("LKG"), ("LKG", ""))

	def test_next_program(self):
		self.assertEqual(common.next_program("Nursery AO", PROGRAMS), "LKG AO")
		self.assertEqual(common.next_program("UKG", PROGRAMS), "Grade 1")
		self.assertEqual(common.next_program("Grade 3 AO", PROGRAMS), "Grade 4 AO")
		# The AO medium ends after Grade 9.
		self.assertEqual(common.next_program("Grade 9 AO", PROGRAMS), "Grade 10")
		# Grade 11 defaults to the natural science stream.
		self.assertEqual(common.next_program("Grade 10", PROGRAMS), "Grade 11 NS")
		self.assertEqual(common.next_program("Grade 11 NS", PROGRAMS), "Grade 12 NS")
		self.assertIsNone(common.next_program("Grade 12 SS", PROGRAMS))

	def test_classify_movement(self):
		self.assertEqual(common.classify_movement(None, "LKG", PROGRAMS), (NEW, ""))
		self.assertEqual(common.classify_movement("Grade 1 AO", "Grade 2 AO", PROGRAMS), (PROMOTED, ""))
		self.assertEqual(common.classify_movement("Grade 9", "Grade 9", PROGRAMS), (REPEATING, ""))
		self.assertEqual(common.classify_movement("Grade 5", "Grade 7", PROGRAMS)[0], SKIPPED)
		self.assertEqual(common.classify_movement("Grade 5", "Grade 4", PROGRAMS)[0], MOVED_DOWN)
		# Expected stream changes are not flagged...
		self.assertEqual(common.classify_movement("Grade 9 AO", "Grade 10", PROGRAMS), (PROMOTED, ""))
		self.assertEqual(common.classify_movement("Grade 10", "Grade 11 NS", PROGRAMS), (PROMOTED, ""))
		# ...unexpected ones are.
		self.assertEqual(
			common.classify_movement("Grade 2", "Grade 3 AO", PROGRAMS), (PROMOTED, "regular -> AO")
		)

	def test_grade_of_section(self):
		self.assertEqual(common.grade_of_section("Grade 12 B"), "Grade 12")
		self.assertEqual(common.grade_of_section("Grade 1 A Branch"), "Grade 1")
		self.assertEqual(common.grade_of_section("Grade 10A"), "Grade 10")
		self.assertEqual(common.grade_of_section("UKGF"), "UKG")
		self.assertIsNone(common.grade_of_section("Sheet1"))

	def test_branch_of_section(self):
		self.assertEqual(common.branch_of_section("Grade 1 A Branch"), "MBS #2")
		self.assertEqual(common.branch_of_section("UKG AO Branch"), "MBS #2")
		self.assertEqual(common.branch_of_section("DD Grade 3 A"), "MBS Dembi Dollo")
		self.assertEqual(common.branch_of_section("Grade 3 A"), "Main")
		self.assertEqual(common.branch_of_section("Grade 3 A", explicit="MBS #2"), "MBS #2")


class TestIdentity(unittest.TestCase):
	def test_school_id(self):
		self.assertEqual(common.normalize_school_id(" m1/13970/18 "), "M1/13970/18")
		self.assertEqual(common.normalize_school_id(4464.0), "4464")
		self.assertEqual(common.normalize_school_id("4464.0"), "4464")
		self.assertEqual(common.normalize_school_id(None), "")

	def test_compare_names(self):
		self.assertEqual(common.compare_names("Amira mudesir kemal", "Amira  Mudesir Kemal"), SAME)
		self.assertEqual(common.compare_names("Fida Girma Ya'e", "Fida Girma Ya’e"), SAME)
		self.assertEqual(common.compare_names("Keti Kasahun Mekonin", "Keti Kasahun Mekonnen"), VARIATION)
		self.assertEqual(common.compare_names("Girma Fida Yae", "Fida Girma Yae"), VARIATION)
		self.assertEqual(common.compare_names("Abel Tesfaye", "Abel Tesfaye Bekele"), VARIATION)
		self.assertEqual(
			common.compare_names("Sabri Abdi Kadir", "Yididiya Anteneh Belete"), CONFLICT
		)
		# Siblings share every name but the first.
		self.assertEqual(common.compare_names("Kena Tesfaye Bekele", "Haset Tesfaye Bekele"), CONFLICT)
		self.assertEqual(common.compare_names("Gift Endalew Rosha", "Toran Endalew Rosha"), CONFLICT)


class TestPasswords(unittest.TestCase):
	def test_local_digits(self):
		for phone in ("+251912345678", "251912345678", "0912345678", "912345678", "+251 91 234 5678"):
			self.assertEqual(common.local_phone_digits(phone), "912345678", phone)
		self.assertEqual(common.local_phone_digits("+251712345678"), "712345678")
		self.assertEqual(common.local_phone_digits("+25191234567"), "")
		self.assertEqual(common.local_phone_digits("+251112345678"), "")
		self.assertEqual(common.local_phone_digits(""), "")

	def test_candidates(self):
		self.assertEqual(
			common.phone_password_candidates("+251912345678"), ["0912345678", "251912345678"]
		)
		self.assertEqual(common.phone_password_candidates(None), [])


class TestIssues(unittest.TestCase):
	def test_worst_and_format(self):
		issues = [
			{"severity": "Info", "message": "a"},
			{"severity": "Blocked", "message": "b"},
			{"severity": "Review", "message": "c"},
		]
		self.assertEqual(common.worst_severity(issues), "Blocked")
		self.assertEqual(common.format_issues(issues).splitlines()[0], "[Blocked] b")
		self.assertIsNone(common.worst_severity([]))


if __name__ == "__main__":
	unittest.main()
