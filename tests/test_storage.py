"""Тесты JSON-хранилища с изоляцией через tempfile.TemporaryDirectory."""

import os
import unittest
from unittest import mock

from src.errors import StorageError
from src.storage import SCHEMA_VERSION, JsonStorage
from tests.factories import TempDirTestCase, make_record, make_registry, \
    make_student


class JsonStorageTest(TempDirTestCase):

    def setUp(self):
        super().setUp()
        self.storage = JsonStorage(self.path("students.json"))

    def test_empty_path_rejected(self):
        for value in ("", None):
            with self.subTest(value=value):
                with self.assertRaises(StorageError):
                    JsonStorage(value)

    def test_save_and_load_round_trip(self):
        registry = make_registry(
            make_student(),
            make_student(record_id="25-002", full_name="Иванова Анна"),
        )
        self.assertEqual(self.storage.save(registry), 2)
        loaded = self.storage.load()
        self.assertEqual(loaded.all(), registry.all())

    def test_save_writes_utf8_and_schema(self):
        self.storage.save(make_registry(make_student()))
        payload = self.read_json("students.json")
        self.assertEqual(payload["version"], SCHEMA_VERSION)
        self.assertEqual(payload["students"][0]["full_name"],
                         "Боков Степан Сергеевич")

    def test_save_creates_missing_directory(self):
        storage = JsonStorage(self.path("nested", "deep", "data.json"))
        storage.save(make_registry())
        self.assertTrue(os.path.exists(storage.path))

    def test_save_leaves_no_temp_files(self):
        self.storage.save(make_registry(make_student()))
        self.assertEqual(os.listdir(self.tmp), ["students.json"])

    def test_failed_save_keeps_old_file_and_cleans_temp(self):
        self.storage.save(make_registry(make_student()))
        with mock.patch("src.storage.os.replace",
                        side_effect=OSError("диск занят")):
            with self.assertRaises(StorageError):
                self.storage.save(make_registry())
        self.assertEqual(os.listdir(self.tmp), ["students.json"])
        self.assertEqual(len(self.storage.load()), 1)

    def test_load_missing_file(self):
        with self.assertRaises(StorageError):
            self.storage.load()
        self.assertEqual(len(self.storage.load(missing_ok=True)), 0)

    def test_load_corrupted_json(self):
        with open(self.storage.path, "w", encoding="utf-8") as handle:
            handle.write("{не json")
        with self.assertRaises(StorageError):
            self.storage.load()

    def test_load_rejects_bad_schema(self):
        bad_payloads = [
            [],
            {"version": 99, "students": []},
            {"students": []},
            {"version": SCHEMA_VERSION, "students": {}},
        ]
        for payload in bad_payloads:
            with self.subTest(payload=payload):
                self.write_json("students.json", payload)
                with self.assertRaises(StorageError):
                    self.storage.load()

    def test_load_reports_bad_record_number(self):
        payload = {"version": SCHEMA_VERSION,
                   "students": [make_record(), make_record(grades=[5, 9])]}
        self.write_json("students.json", payload)
        with self.assertRaisesRegex(StorageError, "№2"):
            self.storage.load()

    def test_load_rejects_duplicates(self):
        payload = {"version": SCHEMA_VERSION,
                   "students": [make_record(), make_record()]}
        self.write_json("students.json", payload)
        with self.assertRaises(StorageError):
            self.storage.load()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
