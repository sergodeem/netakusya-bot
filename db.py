import aiosqlite

# Путь к файлу базы данных
DB_PATH = "bot.db"


async def init_db():
    # """
    # Инициализирует базу данных:
    # - создаёт таблицу reminders для напоминаний,
    # - создаёт таблицу app_state для хранения служебных значений (например, chat_id девушки).
    # """
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица для напоминаний
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                photo_file_id TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        # Таблица для служебных значений (key-value)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
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

