"""Модульные тесты построителя отчётов."""

import unittest

from src.errors import StudentNotFoundError
from src.registry import StudentRegistry
from src.report import ReportBuilder
from tests.factories import make_registry, make_student


class ReportBuilderTest(unittest.TestCase):

    def setUp(self):
        self.registry = make_registry(
            make_student(grades=[5, 5]),
            make_student(record_id="25-002", full_name="Иванова Анна",
                         grades=[4, 5]),
            make_student(record_id="25-003", full_name="Петров Илья",
                         group="Т9-ИП-25-1", grades=[2, 3]),
            make_student(record_id="25-004", full_name="Абрамов Олег",
                         grades=[4, 5]),
        )
        self.builder = ReportBuilder(self.registry)

    def test_group_average(self):
        self.assertEqual(self.builder.group_average("т9-ип-25-2"), 4.67)
        self.assertEqual(self.builder.group_average("Т9-ИП-25-1"), 2.5)

    def test_group_average_unknown_group(self):
        with self.assertRaises(StudentNotFoundError):
            self.builder.group_average("НЕТ")

    def test_group_average_without_grades(self):
        builder = ReportBuilder(make_registry(make_student(grades=[])))
        self.assertEqual(builder.group_average("Т9-ИП-25-2"), 0.0)

    def test_rating_orders_by_average_then_name(self):
        rating = self.builder.rating()
        self.assertEqual([row[1] for row in rating], [
            "Боков Степан Сергеевич", "Абрамов Олег", "Иванова Анна",
            "Петров Илья",
        ])
        self.assertEqual([row[0] for row in rating], [1, 2, 3, 4])

    def test_rating_for_group(self):
        self.assertEqual(self.builder.rating("Т9-ИП-25-1"),
                         [(1, "Петров Илья", 2.5)])

    def test_summary(self):
        self.assertEqual(self.builder.summary(), {
            "total": 4, "groups": 2, "excellent": 1, "debtors": 1,
            "scholarship": 3, "average": 4.12,
        })

    def test_summary_of_empty_registry(self):
        summary = ReportBuilder(StudentRegistry()).summary()
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["average"], 0.0)

    def test_summary_text(self):
        text = self.builder.summary_text()
        self.assertIn("Всего студентов: 4", text)
        self.assertIn("Рейтинг:", text)
        self.assertIn("1. Боков Степан Сергеевич — 5.00", text)

    def test_summary_text_for_group(self):
        text = self.builder.summary_text("Т9-ИП-25-1")
        self.assertIn("Рейтинг группы Т9-ИП-25-1:", text)
        self.assertNotIn("Иванова", text)

    def test_summary_text_without_rating(self):
        text = ReportBuilder(StudentRegistry()).summary_text()
        self.assertNotIn("Рейтинг", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
