"""Консольный сценарий: загрузка → обработка → сохранение → отчёт."""

import argparse
import json
import os
import sys

from src.errors import StorageError, StudentSystemError
from src.report import ReportBuilder
from src.storage import JsonStorage
from src.student import Student

DEMO_STUDENTS = [
    {"record_id": "25-001", "full_name": "Боков Степан Сергеевич",
     "group": "Т9-ИП-25-2", "course": 1, "grades": [5, 5, 5, 5]},
    {"record_id": "25-002", "full_name": "Иванова Анна Петровна",
     "group": "Т9-ИП-25-2", "course": 1, "grades": [5, 4, 4, 5]},
    {"record_id": "25-003", "full_name": "Петров Илья Олегович",
     "group": "Т9-ИП-25-2", "course": 1, "grades": [3, 4, 2, 3]},
    {"record_id": "25-004", "full_name": "Сидорова Мария Игоревна",
     "group": "Т9-ИП-25-1", "course": 1, "grades": [4, 3, 4, 4]},
]


def read_enrollment(path):
    """Прочитать пакет новых студентов (JSON-список записей)."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            records = json.load(handle)
    except (OSError, ValueError) as exc:
        raise StorageError(
            "Не удалось прочитать приказ о зачислении: {0}".format(exc)
        ) from exc
    if not isinstance(records, list):
        raise StorageError("Приказ о зачислении должен быть списком")
    return [Student.from_dict(record) for record in records]


def write_report(path, text):
    """Записать текстовый отчёт в файл."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text + "\n")


def run(data_path, report_path=None, group=None, enroll_path=None,
        demo=False):
    """Интеграционный конвейер системы. Возвращает текст отчёта."""
    storage = JsonStorage(data_path)
    registry = storage.load(missing_ok=True)
    if demo and len(registry) == 0:
        registry.add_many(Student.from_dict(r) for r in DEMO_STUDENTS)
    if enroll_path:
        registry.add_many(read_enrollment(enroll_path))
    storage.save(registry)
    text = ReportBuilder(registry).summary_text(group)
    if report_path:
        write_report(report_path, text)
    return text


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m src.main",
        description="Система учёта студентов",
    )
    parser.add_argument("--data", default="students.json",
                        help="файл ведомости (JSON)")
    parser.add_argument("--report", help="файл для текстового отчёта")
    parser.add_argument("--group", help="группа для рейтинга")
    parser.add_argument("--enroll", help="JSON-пакет новых студентов")
    parser.add_argument("--demo", action="store_true",
                        help="заполнить пустую ведомость демо-данными")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        text = run(args.data, args.report, args.group, args.enroll,
                   args.demo)
    except StudentSystemError as exc:
        print("Ошибка: {0}".format(exc), file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
