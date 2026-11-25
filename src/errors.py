"""Иерархия исключений системы учёта студентов."""


class StudentSystemError(Exception):
    """Базовое исключение системы учёта студентов."""


class ValidationError(StudentSystemError):
    """Нарушены правила валидации входных данных."""


class DuplicateStudentError(StudentSystemError):
    """Студент с таким номером зачётки уже существует."""


class StudentNotFoundError(StudentSystemError):
    """Студент с указанным номером зачётки не найден."""


class StorageError(StudentSystemError):
    """Ошибка работы с файловым хранилищем."""
