import aiosqlite
from datetime import datetime

# Путь к файлу базы данных
DB_PATH = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # напоминания
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                photo_file_id TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        # служебные значения (chat_id девушки, флаги и т.п.)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # НОВОЕ: таблица хотелок
        await db.execute("""
            CREATE TABLE IF NOT EXISTS wishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT,
                photo_file_id TEXT,
                status TEXT NOT NULL DEFAULT 'new', -- new / done / etc
                created_at TEXT NOT NULL
            )
        """)

        await db.commit()


async def add_reminder(text: str | None, photo_file_id: str | None) -> int:
    # """
    # Добавляет новое напоминание в таблицу.
    # text — текст напоминания (может быть None),
    # photo_file_id — file_id фотки (может быть None).
    # Возвращает ID добавленной записи.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO reminders (text, photo_file_id, is_active)
            VALUES (?, ?, 1)
            """,
            (text, photo_file_id)
        )
        await db.commit()
        return cursor.lastrowid


async def list_reminders():
    # """
    # Возвращает список всех напоминаний.
    # Каждый элемент — кортеж (id, text, photo_file_id, is_active).
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, text, photo_file_id, is_active FROM reminders ORDER BY id"
        )
        rows = await cursor.fetchall()
        return rows


async def deactivate_reminder(reminder_id: int) -> bool:
    # """
    # Помечает напоминание как неактивное по его ID.
    # Возвращает True, если хотя бы одна запись была изменена.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE reminders SET is_active = 0 WHERE id = ?",
            (reminder_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def set_girlfriend_chat_id(chat_id: int) -> None:
    # """
    # Сохраняет chat_id твоей девушки в таблицу app_state.
    # Если значение уже есть — перезаписывает.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO app_state (key, value)
            VALUES ('girlfriend_chat_id', ?)
            """,
            (str(chat_id),)
        )
        await db.commit()


async def get_girlfriend_chat_id() -> int | None:
    # """
    # Возвращает chat_id твоей девушки, если он сохранён.
    # Если ещё не сохранён — возвращает None.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM app_state WHERE key = 'girlfriend_chat_id'"
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        try:
            return int(row[0])
        except ValueError:
            return None


async def get_random_active_reminder():
    # """
    # Возвращает одно случайное активное напоминание.
    # Вернёт кортеж (id, text, photo_file_id) или None, если активных нет.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT id, text, photo_file_id
            FROM reminders
            WHERE is_active = 1
            ORDER BY RANDOM()
            LIMIT 1
            """
        )
        row = await cursor.fetchone()
        return row


async def activate_all_reminders() -> int:
    # """
    # Делает все напоминания активными (is_active = 1).
    # Возвращает количество затронутых строк.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE reminders SET is_active = 1"
        )
        await db.commit()
        return cursor.rowcount

async def set_waiting_wish(is_waiting: bool) -> None:
    # """
    # Сохраняет флаг, что мы ждём от девушки сообщение с хотелкой.
    # True -> '1', False -> '0'.
    # """
    value = "1" if is_waiting else "0"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO app_state (key, value)
            VALUES ('girlfriend_waiting_wish', ?)
            """,
            (value,)
        )
        await db.commit()


async def is_waiting_wish() -> bool:
    # """
    # Возвращает True, если бот сейчас ждёт от девушки сообщение с хотелкой.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM app_state WHERE key = 'girlfriend_waiting_wish'"
        )
        row = await cursor.fetchone()
        if row is None:
            return False
        return row[0] == "1"


async def add_wish(user_id: int, text: str | None, photo_file_id: str | None) -> int:
    # """
    # Добавляет хотелку в таблицу wishes.
    # Возвращает ID созданной хотелки.
    # """
    created_at = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO wishes (user_id, text, photo_file_id, status, created_at)
            VALUES (?, ?, ?, 'new', ?)
            """,
            (user_id, text, photo_file_id, created_at)
        )
        await db.commit()
        return cursor.lastrowid


async def list_wishes(limit: int | None = None):
    # """
    # Возвращает список хотелок.
    # Каждый элемент: (id, user_id, text, photo_file_id, status, created_at).
    # """
    query = "SELECT id, user_id, text, photo_file_id, status, created_at FROM wishes ORDER BY id DESC"
    if limit:
        query += f" LIMIT {int(limit)}"

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        return rows
    
async def is_wishes_feature_notified() -> bool:
    # """
    # Возвращает True, если мы уже отправляли девушке уведомление
    # о новой функции с хотелками.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM app_state WHERE key = 'wishes_feature_notified'"
        )
        row = await cursor.fetchone()
        if row is None:
            return False
        return row[0] == "1"


async def set_wishes_feature_notified() -> None:
    # """
    # Помечает, что уведомление о новой функции уже отправлено.
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO app_state (key, value)
            VALUES ('wishes_feature_notified', '1')
            """
        )
        await db.commit()
