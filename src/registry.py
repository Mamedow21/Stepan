"""Управление контингентом студентов."""

from src.errors import (
    DuplicateStudentError,
    StudentNotFoundError,
    ValidationError,
)
from src.student import MAX_COURSE, Student


class StudentRegistry:
    """Реестр студентов с уникальными номерами зачёток."""

    def __init__(self, students=None):
        self._students = {}
        for student in students or []:
            self.add(student)

    @staticmethod
    def _ensure_student(student):
        if not isinstance(student, Student):
            raise ValidationError("В реестр можно добавить только Student")
        return student

    def add(self, student):
        """Добавить студента; номер зачётки должен быть уникальным."""
        self._ensure_student(student)
        if student.record_id in self._students:
            raise DuplicateStudentError(
                "Студент с зачёткой {0} уже есть".format(student.record_id)
            )
        self._students[student.record_id] = student
        return student

    def add_many(self, students):
        """Атомарно добавить пакет студентов (приказ о зачислении)."""
        students = [self._ensure_student(s) for s in students]
        seen = set(self._students)
        for student in students:
            if student.record_id in seen:
                raise DuplicateStudentError(
                    "Студент с зачёткой {0} уже есть".format(
                        student.record_id
                    )
                )
            seen.add(student.record_id)
        for student in students:
            self._students[student.record_id] = student
        return len(students)

    def get(self, record_id):
        """Найти студента по номеру зачётки."""
        try:
            return self._students[record_id]
        except KeyError:
            raise StudentNotFoundError(
                "Студент с зачёткой {0} не найден".format(record_id)
            ) from None

    def remove(self, record_id):
        """Отчислить студента (удалить из реестра)."""
        student = self.get(record_id)
        del self._students[record_id]
        return student

    def promote(self, record_id):
        """Перевести студента на следующий курс."""
        student = self.get(record_id)
        if student.is_debtor():
            raise ValidationError("Должник не может быть переведён на курс")
        if student.course >= MAX_COURSE:
            raise ValidationError("Студент уже на последнем курсе")
        student.course += 1
        return student

    def find_by_group(self, group):
        """Студенты указанной группы, отсортированные по ФИО."""
        key = str(group).strip().upper()
        return sorted(
            (s for s in self._students.values() if s.group == key),
            key=lambda s: s.full_name,
        )

    def find_by_surname(self, surname):
        """Поиск по фамилии без учёта регистра."""
        key = str(surname).strip().lower()
        if not key:
            return []
        return sorted(
            (s for s in self._students.values()
             if s.surname.lower().startswith(key)),
            key=lambda s: s.full_name,
        )

    def excellent_students(self):
        """Список отличников."""
        return [s for s in self.all() if s.is_excellent()]

    def debtors(self):
        """Список должников."""
        return [s for s in self.all() if s.is_debtor()]

    def groups(self):
        """Отсортированный список групп реестра."""
        return sorted({s.group for s in self._students.values()})

    def all(self):
        """Все студенты в порядке номеров зачёток."""
        return [self._students[key] for key in sorted(self._students)]

    def __len__(self):
        return len(self._students)

    def __contains__(self, record_id):
        return record_id in self._students

    def __iter__(self):
        return iter(self.all())
