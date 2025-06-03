class NotFoundError(Exception):
    """
    Исключение: объект не найден (например, при поиске по ID).
    """
    pass


class RelatedEntityNotFoundError(ValueError):
    """
    Исключение: связанная сущность не найдена или неактивна при создании/
    обновлении.
    """
    pass


class DuplicateError(ValueError):
    """
    Исключение: попытка создать или обновить объект с дублирующими
    уникальными полями.
    """
    pass


class DependentActiveChildError(ValueError):
    """
    Исключение: попытка деактивации/удаления сущности с активными зависимыми
    дочерними объектами.
    """
    pass


class AlreadyInactiveError(ValueError):
    """
    Исключение: попытка деактивации уже неактивной сущности.
    """
    pass


class AlreadyActiveError(ValueError):
    """
    Исключение: попытка активировать уже активную сущность.
    """
    pass
