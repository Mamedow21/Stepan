"""Сохранение и загрузка ведомости студентов в формате JSON."""

import json
import os
import tempfile

from src.errors import StorageError, StudentSystemError
from src.registry import StudentRegistry
from src.student import Student

SCHEMA_VERSION = 1


class JsonStorage:
    """Файловое JSON-хранилище реестра студентов."""

    def __init__(self, path):
        if not path:
            raise StorageError("Не указан путь к файлу ведомости")
        self.path = os.fspath(path)

    def save(self, registry):
        """Атомарно сохранить реестр: временный файл + os.replace."""
        payload = {
            "version": SCHEMA_VERSION,
            "students": [student.to_dict() for student in registry],
        }
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            prefix=".students-", suffix=".tmp", dir=directory
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.path)
        except (OSError, TypeError, ValueError) as exc:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise StorageError(
                "Не удалось сохранить ведомость: {0}".format(exc)
            ) from exc
        return len(payload["students"])

    def load(self, missing_ok=False):
        """Загрузить реестр с проверкой схемы и целостности записей."""
        if not os.path.exists(self.path):
            if missing_ok:
                return StudentRegistry()
            raise StorageError(
                "Файл ведомости не найден: {0}".format(self.path)
            )
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError) as exc:
            raise StorageError(
                "Повреждённый файл ведомости: {0}".format(exc)
            ) from exc
        return self._parse(payload)

    @staticmethod
    def _parse(payload):
        if not isinstance(payload, dict):
            raise StorageError("Корень ведомости должен быть объектом")
        if payload.get("version") != SCHEMA_VERSION:
            raise StorageError("Неподдерживаемая версия схемы ведомости")
        records = payload.get("students")
        if not isinstance(records, list):
            raise StorageError("Поле students должно быть списком")
        registry = StudentRegistry()
        for index, record in enumerate(records):
            try:
                registry.add(Student.from_dict(record))
            except StudentSystemError as exc:
                raise StorageError(
                    "Запись №{0} некорректна: {1}".format(index + 1, exc)
                ) from exc
        return registry
