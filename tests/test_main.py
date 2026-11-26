"""Интеграционные тесты консольного конвейера src.main."""

import contextlib
import io
import os
import unittest

from src.errors import DuplicateStudentError, StorageError
from src.main import main, read_enrollment, run
from src.storage import JsonStorage
from tests.factories import TempDirTestCase, make_record


class MainIntegrationTest(TempDirTestCase):

    def setUp(self):
        super().setUp()
        self.data = self.path("students.json")
        self.report = self.path("out", "report.txt")

    def test_demo_pipeline_creates_data_and_report(self):
        text = run(self.data, self.report, demo=True)
        self.assertIn("Всего студентов: 4", text)
        self.assertEqual(len(JsonStorage(self.data).load()), 4)
        with open(self.report, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), text + "\n")

    def test_demo_does_not_overwrite_existing_data(self):
        run(self.data, demo=True)
        enroll = self.write_json("enroll.json", [
            make_record(record_id="25-010", full_name="Новиков Пётр Ильич"),
        ])
        run(self.data, enroll_path=enroll)
        text = run(self.data, demo=True)
        self.assertIn("Всего студентов: 5", text)

    def test_enrollment_and_group_rating(self):
        enroll = self.write_json("enroll.json", [
            make_record(record_id="25-010", full_name="Новиков Пётр Ильич"),
        ])
        text = run(self.data, group="Т9-ИП-25-2", enroll_path=enroll)
        self.assertIn("Рейтинг группы Т9-ИП-25-2:", text)
        self.assertIn("Новиков Пётр Ильич", text)

    def test_enrollment_with_duplicate_keeps_file_unchanged(self):
        run(self.data, demo=True)
        before = self.read_json("students.json")
        enroll = self.write_json("enroll.json", [
            make_record(record_id="25-010", full_name="Новиков Пётр Ильич"),
            make_record(record_id="25-001"),
        ])
        with self.assertRaises(DuplicateStudentError):
            run(self.data, enroll_path=enroll)
        self.assertEqual(self.read_json("students.json"), before)

    def test_read_enrollment_errors(self):
        with self.assertRaises(StorageError):
            read_enrollment(self.path("missing.json"))
        not_list = self.write_json("obj.json", {"students": []})
        with self.assertRaises(StorageError):
            read_enrollment(not_list)

    def test_main_success_exit_code(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["--data", self.data, "--demo",
                         "--report", self.report])
        self.assertEqual(code, 0)
        self.assertIn("Сводка успеваемости", stdout.getvalue())
        self.assertTrue(os.path.exists(self.report))

    def test_main_error_exit_code(self):
        with open(self.data, "w", encoding="utf-8") as handle:
            handle.write("испорчено")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["--data", self.data])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка:", stderr.getvalue())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
