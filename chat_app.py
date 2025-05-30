import sqlite3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from threading import Thread
import queue
import json
from datetime import datetime


class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chat Messenger")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Инициализация базы данных
        self.db_conn = sqlite3.connect('chat_logs.db', check_same_thread=False)
        self.db_cursor = self.db_conn.cursor()
        self._init_db()
        self.current_session_id = self._create_new_session()

        # Настройка интерфейса
        self.setup_ui()

        # Загрузка модели ИИ
        self.load_model()

        # Очередь для межпоточного обмена сообщениями
        self.message_queue = queue.Queue()

        # Запуск проверки очереди сообщений
        self.root.after(100, self.check_queue)

    def _init_db(self):
        """Инициализирует таблицы базы данных, если они не существуют"""
        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            additional_meta TEXT
        )''')

        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            message_text TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )''')

        self.db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            response_text TEXT NOT NULL,
            trigger_name TEXT,
            trigger_details TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES user_messages(message_id)
        )''')

        # Создаем индексы для ускорения запросов
        self.db_cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)
        ''')
        self.db_cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_messages_session ON user_messages(session_id)
        ''')
        self.db_cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_bot_responses_message ON bot_responses(message_id)
        ''')
        self.db_cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_bot_responses_trigger ON bot_responses(trigger_name)
        ''')

        self.db_conn.commit()

    def _create_new_session(self):
        """Создает новую сессию чата в базе данных"""
        meta = {
            "app_version": "1.0",
            "start_time": datetime.now().isoformat(),
            "platform": "desktop"
        }

        self.db_cursor.execute(
            "INSERT INTO sessions (user_id, additional_meta) VALUES (?, ?)",
            ("default_user", json.dumps(meta))
        )
        self.db_conn.commit()
        return self.db_cursor.lastrowid

    def _log_user_message(self, message_text):
        """Логирует сообщение пользователя в базу данных"""
        self.db_cursor.execute(
            "INSERT INTO user_messages (session_id, message_text) VALUES (?, ?)",
            (self.current_session_id, message_text)
        )
        self.db_conn.commit()
        return self.db_cursor.lastrowid

    def _log_bot_response(self, message_id, response_text, trigger_name="model_response"):
        """Логирует ответ бота в базу данных"""
        trigger_details = {
            "model": "GPT",
            "response_time": datetime.now().isoformat(),
            "trigger_type": "auto"
        }

        self.db_cursor.execute(
            """INSERT INTO bot_responses 
               (message_id, response_text, trigger_name, trigger_details) 
               VALUES (?, ?, ?, ?)""",
            (message_id, response_text, trigger_name, json.dumps(trigger_details))
        )
        self.db_conn.commit()

    def setup_ui(self):
        """Настраивает пользовательский интерфейс"""
        # Настройка стилей
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Цветовая схема
        self.bg_color = "#f5f5f5"
        self.sidebar_color = "#2f3136"
        self.chat_bg = "#36393f"
        self.user_msg_color = "#5865f2"
        self.bot_msg_color = "#40444b"
        self.text_color = "#ffffff"
        self.input_bg = "#40444b"

        # Основные фреймы
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Сайдбар
        self.sidebar = ttk.Frame(self.main_frame, width=250, style='Sidebar.TFrame')
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Заголовок сайдбара
        self.sidebar_header = ttk.Label(
            self.sidebar,
            text="Контакты",
            style='SidebarHeader.TLabel',
            font=('Helvetica', 12, 'bold')
        )
        self.sidebar_header.pack(pady=15)

        # Список контактов
        self.contacts_list = tk.Listbox(
            self.sidebar,
            bg="#2f3136",
            fg=self.text_color,
            borderwidth=0,
            highlightthickness=0,
            selectbackground="#5865f2",
            selectforeground=self.text_color,
            font=('Helvetica', 11),
            activestyle='none'
        )
        self.contacts_list.pack(fill=tk.BOTH, expand=True, padx=10)

        # Добавляем контакты
        contacts = ["AI Ассистент", "Техподдержка", "Другой бот"]
        for contact in contacts:
            self.contacts_list.insert(tk.END, contact)
        self.contacts_list.selection_set(0)

        # Основная область чата
        self.chat_frame = ttk.Frame(self.main_frame, style='Chat.TFrame')
        self.chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # История чата
        self.chat_history = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            bg=self.chat_bg,
            fg=self.text_color,
            bd=0,
            font=('Helvetica', 12),
            padx=20,
            pady=20,
            state='disabled'
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True)

        # Настройка тегов для сообщений
        self.chat_history.tag_config('user',
                                     foreground=self.text_color,
                                     background=self.user_msg_color,
                                     lmargin1=100,
                                     rmargin=20,
                                     relief=tk.RAISED,
                                     borderwidth=5)

        self.chat_history.tag_config('bot',
                                     foreground=self.text_color,
                                     background=self.bot_msg_color,
                                     lmargin1=20,
                                     rmargin=100,
                                     relief=tk.RAISED,
                                     borderwidth=5)

        self.chat_history.tag_config('sender',
                                     font=('Helvetica', 9, 'bold'),
                                     spacing1=5)

        # Панель ввода сообщения
        self.input_frame = ttk.Frame(self.chat_frame, style='Input.TFrame')
        self.input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.message_entry = tk.Text(
            self.input_frame,
            height=3,
            wrap=tk.WORD,
            bg=self.input_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            bd=0,
            relief=tk.FLAT,
            font=('Helvetica', 12),
            padx=10,
            pady=8
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self.send_message)
        self.message_entry.bind("<Shift-Return>", lambda e: self.message_entry.insert(tk.INSERT, "\n"))

        # Кнопка отправки
        self.send_button = ttk.Button(
            self.input_frame,
            text="➤",
            command=self.send_message,
            style='Send.TButton',
            width=3
        )
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Настройка стилей
        self.style.configure('Sidebar.TFrame', background=self.sidebar_color)
        self.style.configure('SidebarHeader.TLabel',
                             background=self.sidebar_color,
                             foreground=self.text_color)
        self.style.configure('Chat.TFrame', background=self.chat_bg)
        self.style.configure('Input.TFrame', background=self.chat_bg)
        self.style.configure('Send.TButton',
                             background="#5865f2",
                             foreground=self.text_color,
                             font=('Helvetica', 12),
                             borderwidth=0)

        # Приветственное сообщение
        self.add_message("AI Ассистент", "Привет! Я ваш виртуальный помощник. Чем могу помочь?", "bot")

    def load_model(self):
        """Загружает модель ИИ в отдельном потоке"""
        self.model_path = "./chatbot-gpt-model"

        # Показываем сообщение о загрузке
        self.add_message("Система", "Загружаю модель...", "bot")

        # Запускаем загрузку в отдельном потоке
        Thread(target=self._load_model_thread, daemon=True).start()

    def _load_model_thread(self):
        """Поток для загрузки модели ИИ"""
        try:
            # Загрузка токенизатора и модели
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)

            self.message_queue.put(("Система", "Модель успешно загружена!", "bot"))
        except Exception as e:
            self.message_queue.put(("Система", f"Ошибка загрузки модели: {str(e)}", "bot"))

    def check_queue(self):
        """Проверяет очередь сообщений и выводит их в интерфейс"""
        try:
            while True:
                sender, message, msg_type = self.message_queue.get_nowait()
                self.add_message(sender, message, msg_type)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def add_message(self, sender, message, msg_type):
        """Добавляет сообщение в историю чата"""
        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, f"{sender}\n", 'sender')
        self.chat_history.insert(tk.END, f"{message}\n\n", msg_type)
        self.chat_history.see(tk.END)
        self.chat_history.configure(state='disabled')

    def send_message(self, event=None):
        """Обрабатывает отправку сообщения пользователем"""
        message = self.message_entry.get("1.0", tk.END).strip()
        if not message:
            return

        # Добавляем сообщение пользователя в интерфейс
        self.add_message("Вы", message, 'user')

        # Логируем сообщение пользователя в БД
        message_id = self._log_user_message(message)

        self.message_entry.delete("1.0", tk.END)

        # Генерируем ответ в отдельном потоке
        Thread(target=self.generate_response, args=(message, message_id), daemon=True).start()

    def generate_response(self, message, user_message_id):
        """Генерирует ответ ИИ на сообщение пользователя"""
        try:
            if not hasattr(self, 'model') or not hasattr(self, 'tokenizer'):
                self.message_queue.put(("Система", "Модель еще не загружена...", "bot"))
                return

            prompt = f"Ввод: {message}\nОтвет:"
            input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)

            with torch.no_grad():
                output_ids = self.model.generate(
                    input_ids,
                    max_new_tokens=100,
                    do_sample=True,
                    top_k=50,
                    top_p=0.95,
                    temperature=0.8,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            response = self.tokenizer.decode(output_ids[0][input_ids.shape[1]:], skip_special_tokens=True)
            response = response.strip()

            # Логируем ответ бота в БД
            self._log_bot_response(user_message_id, response)

            self.message_queue.put(("AI Ассистент", response, "bot"))
        except Exception as e:
            self.message_queue.put(("Система", f"Ошибка генерации: {str(e)}", "bot"))

    def on_closing(self):
        """Обрабатывает закрытие приложения"""
        self.db_conn.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()