import os


DEFAULT_TARIFFS = {
    "basic": 990000,
    "standard": 1990000,
    "premium": 2990000
}

# Для дальнейшего разворачивания должно быть в БД, как отдельная сущность

PROMO_CODES = {
    "KVITTO10": 10
}

# Локально сохраняется прежний путь; Docker передаёт путь к постоянному тому.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./payments.db")
SQL_ECHO = os.getenv("SQL_ECHO", "true").lower() in {"1", "true", "yes", "on"}
