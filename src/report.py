"""Аналитические отчёты по успеваемости студентов."""

from src.errors import StudentNotFoundError


class ReportBuilder:
    """Построитель отчётов на основе реестра студентов."""

    def __init__(self, registry):
        self.registry = registry

    def group_average(self, group):
        """Средний балл группы по всем оценкам её студентов."""
        students = self.registry.find_by_group(group)
        if not students:
            raise StudentNotFoundError("Группа {0} не найдена".format(group))
        grades = [grade for student in students for grade in student.grades]
        if not grades:
            return 0.0
        return round(sum(grades) / len(grades), 2)

    def rating(self, group=None):
        """Рейтинг: по убыванию среднего балла, при равенстве — по ФИО."""
        if group is None:
            students = self.registry.all()
        else:
            students = self.registry.find_by_group(group)
        ordered = sorted(students, key=lambda s: (-s.average(), s.full_name))
        return [
            (place, student.full_name, student.average())
            for place, student in enumerate(ordered, start=1)
        ]

    def summary(self):
        """Сводные показатели успеваемости."""
        students = self.registry.all()
        total = len(students)
        with_grades = [s for s in students if s.grades]
        overall = 0.0
        if with_grades:
            overall = round(
                sum(s.average() for s in with_grades) / len(with_grades), 2
            )
        return {
            "total": total,
            "groups": len(self.registry.groups()),
            "excellent": len(self.registry.excellent_students()),
            "debtors": len(self.registry.debtors()),
            "scholarship": sum(1 for s in students if s.has_scholarship()),
            "average": overall,
        }

    def summary_text(self, group=None):
        """Текстовая сводка успеваемости для вывода в консоль или файл."""
        data = self.summary()
        lines = [
            "Сводка успеваемости",
            "Всего студентов: {0}".format(data["total"]),
            "Групп: {0}".format(data["groups"]),
            "Отличников: {0}".format(data["excellent"]),
            "Должников: {0}".format(data["debtors"]),
            "Получают стипендию: {0}".format(data["scholarship"]),
            "Средний балл: {0:.2f}".format(data["average"]),
        ]
        rating = self.rating(group)
        if rating:
            title = "Рейтинг" if group is None else "Рейтинг группы " + group
            lines.append(title + ":")
            for place, name, average in rating:
                lines.append("{0}. {1} — {2:.2f}".format(place, name, average))
        return "\n".join(lines)
