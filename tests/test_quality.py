"""Тесты качества: анализ причинно-следственных связей C1..C8 -> E1..E8.

Причины:
  C1 - реквизиты студента корректны (зачётка, ФИО, группа, курс 1..6);
  C2 - все оценки - целые числа в диапазоне 2..5;
  C3 - список оценок непуст;
  C4 - среди оценок есть неудовлетворительная (2);
  C5 - минимальная оценка не ниже 4;
  C6 - все оценки равны 5;
  C7 - номер зачётки уже есть в реестре;
  C8 - студент учится на последнем (6-м) курсе.

Следствия:
  E1 = C1 & C2 & !C7       - студент зарегистрирован в реестре;
  E2 = !C1 | !C2           - ValidationError, реестр не изменён;
  E3 = C1 & C2 & C7        - DuplicateStudentError, реестр не изменён;
  E4 = E1 & C3 & C6        - студент признан отличником;
  E5 = E1 & C4             - студент признан должником;
  E6 = E1 & C3 & C5        - студенту назначена стипендия;
  E7 = E1 & !C4 & !C8      - студент переведён на следующий курс;
  E8 = E1 & (C4 | C8)      - в переводе отказано (ValidationError).

Ограничения: C6 -> C5 -> !C4; !C3 -> !C4 & !C5 & !C6.
"""

import unittest

from src.errors import DuplicateStudentError, ValidationError
from src.registry import StudentRegistry
from src.student import Student
from tests.factories import make_record, make_student

ALL_EFFECTS = {"E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"}

DECISION_TABLE = {
    "T01": (make_record(grades=[5, 5, 5]), {"E1", "E4", "E6", "E7"}),
    "T02": (make_record(grades=[5, 4, 4]), {"E1", "E6", "E7"}),
    "T03": (make_record(grades=[4, 3, 5]), {"E1", "E7"}),
    "T04": (make_record(grades=[5, 2, 4]), {"E1", "E5", "E8"}),
    "T05": (make_record(grades=[]), {"E1", "E7"}),
    "T06": (make_record(course=6, grades=[5, 5]), {"E1", "E4", "E6", "E8"}),
    "T07": (make_record(course=6, grades=[2, 3]), {"E1", "E5", "E8"}),
    "T08": (make_record(record_id="AB-1"), {"E2"}),
    "T09": (make_record(full_name="Боков"), {"E2"}),
    "T10": (make_record(course=7), {"E2"}),
    "T11": (make_record(grades=[5, 7]), {"E2"}),
}


def observe(record, registry=None):
    """Пропустить запись через систему и вернуть множество следствий."""
    registry = StudentRegistry() if registry is None else registry
    try:
        student = Student.from_dict(record)
    except ValidationError:
        return {"E2"}
    try:
        registry.add(student)
    except DuplicateStudentError:
        return {"E3"}
    effects = {"E1"}
    if student.is_excellent():
        effects.add("E4")
    if student.is_debtor():
        effects.add("E5")
    if student.has_scholarship():
        effects.add("E6")
    try:
        registry.promote(student.record_id)
    except ValidationError:
        effects.add("E8")
    else:
        effects.add("E7")
    return effects


class CauseEffectTableTest(unittest.TestCase):
    """Каждая строка таблицы решений превращена в отдельный тест."""

    def check_row(self, row_id):
        record, expected = DECISION_TABLE[row_id]
        self.assertEqual(observe(record), expected, row_id)

    def test_t01_excellent_student(self):
        self.check_row("T01")

    def test_t02_scholarship_without_excellence(self):
        self.check_row("T02")

    def test_t03_satisfactory_grades(self):
        self.check_row("T03")

    def test_t04_debtor_not_promoted(self):
        self.check_row("T04")

    def test_t05_no_grades_yet(self):
        self.check_row("T05")

    def test_t06_last_course_excellent_not_promoted(self):
        self.check_row("T06")

    def test_t07_last_course_debtor(self):
        self.check_row("T07")

    def test_t08_invalid_record_id(self):
        self.check_row("T08")

    def test_t09_invalid_full_name(self):
        self.check_row("T09")

    def test_t10_course_out_of_range(self):
        self.check_row("T10")

    def test_t11_grade_out_of_range_from_json(self):
        """Регрессия BR-01: from_dict обязан валидировать оценки."""
        self.check_row("T11")

    def test_t12_duplicate_record_id(self):
        registry = StudentRegistry([make_student()])
        self.assertEqual(observe(make_record(), registry), {"E3"})
        self.assertEqual(len(registry), 1)

    def test_t13_duplicate_in_batch_rejected_atomically(self):
        """Регрессия BR-02: пакет с дубликатом не меняет реестр."""
        registry = StudentRegistry([make_student()])
        batch = [
            make_student(record_id="25-010", full_name="Новиков Пётр Ильич"),
            make_student(),
        ]
        with self.assertRaises(DuplicateStudentError):
            registry.add_many(batch)
        self.assertEqual(len(registry), 1)
        self.assertNotIn("25-010", registry)


class CauseEffectPropertiesTest(unittest.TestCase):
    """Ограничения между причинами и взаимоисключение следствий."""

    GRADE_SETS = ([5], [5, 5, 4], [4, 4], [3, 4], [2], [2, 5, 5], [3, 3])

    def test_constraint_c6_implies_c5_implies_not_c4(self):
        for grades in self.GRADE_SETS:
            with self.subTest(grades=grades):
                student = make_student(grades=grades)
                if student.is_excellent():
                    self.assertTrue(student.has_scholarship())
                if student.has_scholarship():
                    self.assertFalse(student.is_debtor())

    def test_no_grades_masks_status_causes(self):
        student = make_student(grades=[])
        self.assertEqual(student.average(), 0.0)
        self.assertFalse(student.is_excellent())
        self.assertFalse(student.is_debtor())
        self.assertFalse(student.has_scholarship())

    def test_e2_leaves_registry_unchanged(self):
        registry = StudentRegistry()
        with self.assertRaises(ValidationError):
            registry.add(Student("25-002", "Иванова Анна", "Т9", 0))
        self.assertEqual(len(registry), 0)

    def test_e7_increments_course_by_one(self):
        registry = StudentRegistry([make_student(course=3)])
        registry.promote("25-001")
        self.assertEqual(registry.get("25-001").course, 4)

    def test_e8_keeps_course(self):
        registry = StudentRegistry([make_student(grades=[2, 5])])
        with self.assertRaises(ValidationError):
            registry.promote("25-001")
        self.assertEqual(registry.get("25-001").course, 1)

    def test_effects_are_mutually_exclusive(self):
        for row_id, (record, _) in sorted(DECISION_TABLE.items()):
            with self.subTest(row=row_id):
                effects = observe(record)
                self.assertEqual(len(effects & {"E1", "E2", "E3"}), 1)
                if "E1" in effects:
                    self.assertEqual(len(effects & {"E7", "E8"}), 1)

    def test_decision_table_covers_all_effects(self):
        covered = set().union(*(e for _, e in DECISION_TABLE.values()))
        covered.add("E3")
        self.assertEqual(covered, ALL_EFFECTS)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
