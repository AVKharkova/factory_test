class NotFoundError(Exception):
    """Исключение для ошибок вида не найдено."""
    pass


class RelatedEntityNotFoundError(ValueError):
    """Исключение еслисвязанная сущность не найдена при создании/обновлении."""
    pass


class DuplicateError(ValueError):
    """Исключение для дублирующихся записей."""
    pass
