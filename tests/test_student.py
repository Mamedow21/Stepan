"""Модульные тесты модели Student: классы эквивалентности и границы."""

import unittest

from src.errors import ValidationError
from src.student import MAX_COURSE, MIN_COURSE, Student
from tests.factories import make_record, make_student


class StudentValidationTest(unittest.TestCase):

    def test_valid_student_is_normalized(self):
        student = Student(" 25-001 ", "  Боков   Степан  Сергеевич ",
                          " т9-ип-25-2 ", 1, [5, 4])
        self.assertEqual(student.record_id, "25-001")
        self.assertEqual(student.full_name, "Боков Степан Сергеевич")
        self.assertEqual(student.group, "Т9-ИП-25-2")
        self.assertEqual(student.grades, [5, 4])

    def test_invalid_record_id(self):
        for value in (None, "", "   ", 25001, "25/001", "AB-1"):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    make_student(record_id=value)

    def test_invalid_full_name(self):
        for value in (None, "", "  ", "Боков", 42):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    make_student(full_name=value)

    def test_invalid_group(self):
        for value in (None, "", "   ", 92):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    make_student(group=value)

    def test_course_boundaries(self):
        for value in (MIN_COURSE, MIN_COURSE + 1, MAX_COURSE - 1, MAX_COURSE):
            with self.subTest(value=value):
                self.assertEqual(make_student(course=value).course, value)
        for value in (MIN_COURSE - 1, MAX_COURSE + 1, "1", 1.0, True):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    make_student(course=value)

    def test_grade_boundaries(self):
        for value in (2, 3, 4, 5):
            with self.subTest(value=value):
                self.assertEqual(make_student(grades=[value]).grades, [value])
        for value in (1, 6, 0, -5, 4.5, "5", None, False):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    make_student(grades=[value])

    def test_grades_must_be_sequence(self):
        with self.assertRaises(ValidationError):
            make_student(grades="545")
        self.assertEqual(make_student(grades=(5, 4)).grades, [5, 4])
        self.assertEqual(make_student(grades=None).grades, [])


class StudentBehaviourTest(unittest.TestCase):

    def test_add_grade_is_chainable(self):
        student = make_student(grades=[])
        self.assertIs(student.add_grade(4).add_grade(5), student)
        self.assertEqual(student.grades, [4, 5])

    def test_failed_add_grade_keeps_list(self):
        student = make_student(grades=[5])
        with self.assertRaises(ValidationError):
            student.add_grade(9)
        self.assertEqual(student.grades, [5])

    def test_average(self):
        self.assertEqual(make_student(grades=[]).average(), 0.0)
        self.assertEqual(make_student(grades=[5, 4, 4]).average(), 4.33)
        self.assertEqual(make_student(grades=[2]).average(), 2.0)

    def test_status_predicates(self):
        cases = [
            ([5, 5], True, False, True),
            ([5, 4], False, False, True),
            ([4, 3], False, False, False),
            ([5, 2], False, True, False),
            ([], False, False, False),
        ]
        for grades, excellent, debtor, scholarship in cases:
            with self.subTest(grades=grades):
                student = make_student(grades=grades)
                self.assertIs(student.is_excellent(), excellent)
                self.assertIs(student.is_debtor(), debtor)
                self.assertIs(student.has_scholarship(), scholarship)

    def test_surname(self):
        self.assertEqual(make_student().surname, "Боков")


class StudentSerializationTest(unittest.TestCase):

    def test_round_trip(self):
        student = make_student()
        self.assertEqual(Student.from_dict(student.to_dict()), student)

    def test_to_dict_returns_copy_of_grades(self):
        student = make_student()
        data = student.to_dict()
        data["grades"].append(2)
        self.assertEqual(student.grades, [5, 4, 5])

    def test_from_dict_rejects_non_dict(self):
        for value in (None, [], "запись"):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    Student.from_dict(value)

    def test_from_dict_validates_grades(self):
        """Регрессия BR-01."""
        for grades in ([5, 7], [1], ["5"], "55"):
            with self.subTest(grades=grades):
                with self.assertRaises(ValidationError):
                    Student.from_dict(make_record(grades=grades))

    def test_from_dict_without_grades(self):
        record = make_record()
        del record["grades"]
        self.assertEqual(Student.from_dict(record).grades, [])

    def test_equality_and_repr(self):
        self.assertEqual(make_student(), make_student())
        self.assertNotEqual(make_student(), make_student(course=2))
        self.assertNotEqual(make_student(), "25-001")
        self.assertIn("25-001", repr(make_student()))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
