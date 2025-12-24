import string
import random
from collections import defaultdict
from datetime import datetime


# Основное хранилище ссылок
# short_id -> данные ссылки
urls = {}

# Статистика переходов
# short_id -> {
#   "clicks": int,
#   "ips": set(str),
#   "ip_clicks": dict(ip -> count)
# }
stats = defaultdict(lambda: {
    "clicks": 0,
    "ips": set(),
    "ip_clicks": defaultdict(int)
})

# Учёт созданных ссылок пользователями
# user_id -> {
#   "count": int,
#   "date": YYYY-MM-DD
# }
user_limits = {}


def generate_short_id(length: int = 6) -> str:
    """
    Генерирует уникальный идентификатор короткой ссылки
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def can_create_link(user_id: str) -> bool:
    """
    Проверяет, может ли пользователь создать новую ссылку
    (не более 10 ссылок в сутки)
    """
    today = datetime.utcnow().date()

    if user_id not in user_limits:
        user_limits[user_id] = {"count": 0, "date": today}

    # Если новый день — сбрасываем счётчик
    if user_limits[user_id]["date"] != today:
        user_limits[user_id]["count"] = 0
        user_limits[user_id]["date"] = today

    return user_limits[user_id]["count"] < 10


def register_link_creation(user_id: str):
    """
    Регистрирует факт создания ссылки пользователем
    """
    user_limits[user_id]["count"] += 1


def register_click(short_id: str, ip: str) -> bool:
    """
    Регистрирует переход по ссылке.
    Возвращает False, если превышен лимит (100 кликов с одного IP в сутки)
    """
    today = datetime.utcnow().date()

    # Инициализация даты для IP
    if "date" not in stats[short_id]:
        stats[short_id]["date"] = today

    # Новый день — сбрасываем IP-статистику
    if stats[short_id]["date"] != today:
        stats[short_id]["ip_clicks"].clear()
        stats[short_id]["ips"].clear()
        stats[short_id]["clicks"] = 0
        stats[short_id]["date"] = today

    # Проверка лимита
    if stats[short_id]["ip_clicks"][ip] >= 100:
        return False

    stats[short_id]["clicks"] += 1
    stats[short_id]["ip_clicks"][ip] += 1
    stats[short_id]["ips"].add(ip)

    return True
