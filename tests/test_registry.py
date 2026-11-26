"""Модульные тесты реестра студентов."""

import unittest

from src.errors import (
    DuplicateStudentError,
    StudentNotFoundError,
    ValidationError,
)
from src.registry import StudentRegistry
from tests.factories import make_registry, make_student


class StudentRegistryTest(unittest.TestCase):

    def setUp(self):
        self.bokov = make_student()
        self.ivanova = make_student(record_id="25-002",
                                    full_name="Иванова Анна Петровна",
                                    grades=[5, 5])
        self.petrov = make_student(record_id="25-003",
                                   full_name="Петров Илья Олегович",
                                   group="Т9-ИП-25-1", grades=[3, 2])
        self.registry = make_registry(self.petrov, self.bokov, self.ivanova)

    def test_add_and_get(self):
        self.assertEqual(len(self.registry), 3)
        self.assertIs(self.registry.get("25-001"), self.bokov)
        self.assertIn("25-002", self.registry)
        self.assertNotIn("99-999", self.registry)

    def test_add_rejects_non_student(self):
        with self.assertRaises(ValidationError):
            self.registry.add({"record_id": "25-009"})

    def test_add_rejects_duplicate(self):
        with self.assertRaises(DuplicateStudentError):
            self.registry.add(make_student())
        self.assertEqual(len(self.registry), 3)

    def test_get_unknown_raises(self):
        with self.assertRaises(StudentNotFoundError):
            self.registry.get("99-999")

    def test_remove(self):
        self.assertIs(self.registry.remove("25-003"), self.petrov)
        self.assertEqual(len(self.registry), 2)
        with self.assertRaises(StudentNotFoundError):
            self.registry.remove("25-003")

    def test_add_many_success(self):
        batch = (make_student(record_id="25-0{0}".format(i),
                              full_name="Студент Номер{0}".format(i))
                 for i in range(10, 13))
        self.assertEqual(self.registry.add_many(batch), 3)
        self.assertEqual(len(self.registry), 6)

    def test_add_many_duplicate_inside_batch_is_atomic(self):
        """Регрессия BR-02: дубликат внутри самого пакета."""
        batch = [make_student(record_id="25-020", full_name="Новый Студент"),
                 make_student(record_id="25-020", full_name="Другой Студент")]
        with self.assertRaises(DuplicateStudentError):
            self.registry.add_many(batch)
        self.assertEqual(len(self.registry), 3)

    def test_add_many_invalid_item_is_atomic(self):
        batch = [make_student(record_id="25-021", full_name="Новый Студент"),
                 "не студент"]
        with self.assertRaises(ValidationError):
            self.registry.add_many(batch)
        self.assertNotIn("25-021", self.registry)

    def test_promote(self):
        self.assertEqual(self.registry.promote("25-001").course, 2)

    def test_promote_debtor_refused(self):
        with self.assertRaises(ValidationError):
            self.registry.promote("25-003")
        self.assertEqual(self.petrov.course, 1)

    def test_promote_last_course_refused(self):
        self.registry.add(make_student(record_id="20-001",
                                       full_name="Старший Курсант",
                                       course=6))
        with self.assertRaises(ValidationError):
            self.registry.promote("20-001")

    def test_promote_unknown_raises(self):
        with self.assertRaises(StudentNotFoundError):
            self.registry.promote("99-999")

    def test_find_by_group_is_sorted_and_case_insensitive(self):
        found = self.registry.find_by_group(" т9-ип-25-2 ")
        self.assertEqual(found, [self.bokov, self.ivanova])
        self.assertEqual(self.registry.find_by_group("НЕТ"), [])

    def test_find_by_surname(self):
        self.assertEqual(self.registry.find_by_surname("бок"), [self.bokov])
        self.assertEqual(self.registry.find_by_surname("ПЕТРОВ"),
                         [self.petrov])
        self.assertEqual(self.registry.find_by_surname("   "), [])
        self.assertEqual(self.registry.find_by_surname("Степан"), [])

    def test_status_lists(self):
        self.assertEqual(self.registry.excellent_students(), [self.ivanova])
        self.assertEqual(self.registry.debtors(), [self.petrov])

    def test_groups_and_order(self):
        self.assertEqual(self.registry.groups(), ["Т9-ИП-25-1", "Т9-ИП-25-2"])
        self.assertEqual([s.record_id for s in self.registry],
                         ["25-001", "25-002", "25-003"])

    def test_empty_registry(self):
        registry = StudentRegistry()
        self.assertEqual(len(registry), 0)
        self.assertEqual(registry.all(), [])
        self.assertEqual(registry.groups(), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
