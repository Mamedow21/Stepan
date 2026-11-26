"""Фабрики тестовых данных и базовый класс с временным каталогом."""

import json
import os
import tempfile
import unittest

from src.registry import StudentRegistry
from src.student import Student

VALID_RECORD = {
    "record_id": "25-001",
    "full_name": "Боков Степан Сергеевич",
    "group": "Т9-ИП-25-2",
    "course": 1,
    "grades": [5, 4, 5],
}


def make_record(**overrides):
    """Корректная запись студента с заменой отдельных полей."""
    record = dict(VALID_RECORD)
    record["grades"] = list(VALID_RECORD["grades"])
    record.update(overrides)
    return record


def make_student(**overrides):
    """Корректный объект Student с заменой отдельных полей."""
    return Student(**make_record(**overrides))


def make_registry(*students):
    """Реестр, заполненный переданными студентами."""
    return StudentRegistry(list(students))


class TempDirTestCase(unittest.TestCase):
    """Каждый тест получает собственный tempfile.TemporaryDirectory."""

    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory(prefix="stepan-test-")
        self.tmp = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()
        super().tearDown()

    def path(self, *parts):
        return os.path.join(self.tmp, *parts)

    def write_json(self, name, payload):
        target = self.path(name)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
        return target

    def read_json(self, name):
        with open(self.path(name), "r", encoding="utf-8") as handle:
            return json.load(handle)
