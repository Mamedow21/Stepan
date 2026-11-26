"""Модель студента и правила валидации его данных."""

from src.errors import ValidationError

MIN_GRADE = 2
MAX_GRADE = 5
MIN_COURSE = 1
MAX_COURSE = 6
FAIL_GRADE = 2
SCHOLARSHIP_MIN_GRADE = 4
EXCELLENT_GRADE = 5


class Student:
    """Студент: номер зачётки, ФИО, группа, курс и список оценок."""

    def __init__(self, record_id, full_name, group, course, grades=None):
        self.record_id = self._validate_record_id(record_id)
        self.full_name = self._validate_full_name(full_name)
        self.group = self._validate_group(group)
        self.course = self._validate_course(course)
        self.grades = []
        if grades is not None and not isinstance(grades, (list, tuple)):
            raise ValidationError("Оценки должны быть переданы списком")
        for grade in grades or []:
            self.add_grade(grade)

    @staticmethod
    def _validate_record_id(record_id):
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValidationError("Номер зачётки должен быть непустой строкой")
        value = record_id.strip()
        if not value.replace("-", "").isdigit():
            raise ValidationError(
                "Номер зачётки может содержать только цифры и дефис"
            )
        return value

    @staticmethod
    def _validate_full_name(full_name):
        if not isinstance(full_name, str) or not full_name.strip():
            raise ValidationError("ФИО должно быть непустой строкой")
        parts = full_name.split()
        if len(parts) < 2:
            raise ValidationError("ФИО должно состоять минимум из двух слов")
        return " ".join(parts)

    @staticmethod
    def _validate_group(group):
        if not isinstance(group, str) or not group.strip():
            raise ValidationError("Группа должна быть непустой строкой")
        return group.strip().upper()

    @staticmethod
    def _validate_course(course):
        if isinstance(course, bool) or not isinstance(course, int):
            raise ValidationError("Курс должен быть целым числом")
        if not MIN_COURSE <= course <= MAX_COURSE:
            raise ValidationError(
                "Курс должен быть в диапазоне {0}..{1}".format(
                    MIN_COURSE, MAX_COURSE
                )
            )
        return course

    @staticmethod
    def _validate_grade(grade):
        if isinstance(grade, bool) or not isinstance(grade, int):
            raise ValidationError("Оценка должна быть целым числом")
        if not MIN_GRADE <= grade <= MAX_GRADE:
            raise ValidationError(
                "Оценка должна быть в диапазоне {0}..{1}".format(
                    MIN_GRADE, MAX_GRADE
                )
            )
        return grade

    @property
    def surname(self):
        """Фамилия студента (первое слово ФИО)."""
        return self.full_name.split()[0]

    def add_grade(self, grade):
        """Добавить оценку с проверкой допустимого диапазона."""
        self.grades.append(self._validate_grade(grade))
        return self

    def average(self):
        """Средний балл студента (0.0, если оценок нет)."""
        if not self.grades:
            return 0.0
        return round(sum(self.grades) / len(self.grades), 2)

    def is_excellent(self):
        """Отличник: есть оценки, и все они равны 5."""
        return bool(self.grades) and all(
            grade == EXCELLENT_GRADE for grade in self.grades
        )

    def is_debtor(self):
        """Должник: есть хотя бы одна неудовлетворительная оценка."""
        return any(grade <= FAIL_GRADE for grade in self.grades)

    def has_scholarship(self):
        """Стипендия: есть оценки, и все они не ниже 4."""
        return bool(self.grades) and min(self.grades) >= SCHOLARSHIP_MIN_GRADE

    def to_dict(self):
        """Сериализовать студента в словарь."""
        return {
            "record_id": self.record_id,
            "full_name": self.full_name,
            "group": self.group,
            "course": self.course,
            "grades": list(self.grades),
        }

    @classmethod
    def from_dict(cls, data):
        """Восстановить студента из словаря (например, из JSON)."""
        if not isinstance(data, dict):
            raise ValidationError("Запись студента должна быть словарём")
        return cls(
            record_id=data.get("record_id"),
            full_name=data.get("full_name"),
            group=data.get("group"),
            course=data.get("course"),
            grades=data.get("grades"),
        )

    def __eq__(self, other):
        if not isinstance(other, Student):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    def __repr__(self):
        return "Student({0!r}, {1!r}, {2!r})".format(
            self.record_id, self.full_name, self.group
        )
