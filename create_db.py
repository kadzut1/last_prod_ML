import sqlite3


def create_database(db_name='chat_logs.db'):
    """Создает базу данных SQLite с таблицами для логов чата"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            additional_meta TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            message_text TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            response_text TEXT NOT NULL,
            trigger_name TEXT,
            trigger_details TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES user_messages(message_id)
        )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_messages_session ON user_messages(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_responses_message ON bot_responses(message_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bot_responses_trigger ON bot_responses(trigger_name)')

        conn.commit()
        print(f"База данных {db_name} успешно создана с необходимыми таблицами.")

    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    create_database()