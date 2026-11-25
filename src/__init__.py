"""Система учёта студентов (Вариант 5 лабораторной работы №4)."""

from src.errors import (
    DuplicateStudentError,
    StorageError,
    StudentNotFoundError,
    StudentSystemError,
    ValidationError,
)
from src.student import Student
from src.registry import StudentRegistry
from src.storage import JsonStorage
from src.report import ReportBuilder

__all__ = [
    "Student",
    "StudentRegistry",
    "JsonStorage",
    "ReportBuilder",
    "StudentSystemError",
    "ValidationError",
    "DuplicateStudentError",
    "StudentNotFoundError",
    "StorageError",
]

__version__ = "1.0.0"
