# 🤖 Telegram Chat AI — ИИ-ассистент на базе GPT

Этот проект — персональный ИИ-чат-ассистент, построенный на основе модели GPT, дообученной на 15,000 сообщений из Telegram-чатов. Приложение представляет собой графический чат (на `tkinter`), где все сообщения пользователя и ответы ИИ логируются в SQLite-базу данных.

## 🔧 Структура проекта

```plaintext
├── chatbot-gpt-model/           # Обученная модель
├── result.json                  # Telegram данные (экспорт)
├── parser.py                    # Парсер Telegram сообщений
├── train_model.py               # Скрипт дообучения модели
├── chat_app.py                  # Графическое приложение (tkinter)
├── create_db.py                 # Инициализация базы данных
├── chat_logs.db                 # SQLite база данных
├── README.md                    # Документация
└── requirements.txt             # Зависимости
```

## 📦 Установка

```bash
pip install -r requirements.txt
```

`requirements.txt` может содержать, например:

```txt
transformers
torch
pandas
datasets
tk
```

## 🧠 Обучение модели

Модель дообучалась на основе `sberbank-ai/rugpt3small_based_on_gpt2`.

### 📥 Данные

- Данные экспортированы из Telegram в формате `result.json`.
- Использовался собственный парсер (`parser.py`) для извлечения цепочек: **вопрос** → **ответ**.

```python
df = pd.read_csv('/content/my_messages1.csv')[['text', 'target']]
df['text_pair'] = 'Ввод: ' + df['text'] + '\nОтвет: ' + df['target']
```

### ⚙️ Обучение (`train_model.py`)

- Используется `Trainer` из `transformers`.
- Цикл адаптируется под `loss` (уменьшение LR, увеличение эпох).
- Целевая ошибка: `loss <= 0.4`.

### 🧠 Модель

```python
tokenizer = AutoTokenizer.from_pretrained("sberbank-ai/rugpt3small_based_on_gpt2")
model = AutoModelForCausalLM.from_pretrained(...)
```

Обученная модель сохраняется в `chatbot-gpt-model/`.

## 💬 Интерфейс (chat_app.py)

Запускается через:

```bash
python chat_app.py
```

### Возможности:

- Графический интерфейс (Tkinter)
- Ввод текста пользователем
- Генерация ответа с использованием дообученной модели
- Логирование всех сообщений в базу данных
- Очередь обработки сообщений через `Thread` и `Queue`

## 🧾 База данных (`chat_logs.db`)

Инициализируется через:

```bash
python create_db.py
```

Содержит 3 таблицы:

| Таблица         | Назначение                                 |
|------------------|--------------------------------------------|
| `sessions`       | Информация о сессиях                      |
| `user_messages`  | Все сообщения от пользователя            |
| `bot_responses`  | Ответы ИИ (включая мета-инфу о генерации) |

## 📊 Telegram парсер (`parser.py`)

Используется для разбора Telegram JSON:

```bash
python parser.py
```

- Открывает `result.json`
- Ищет сообщения не от пользователя
- Связывает их с последующим сообщением пользователя (предположительно, ответ)
- Сохраняет в `.csv` файл: `text`, `target`



## 🧑‍💻 Автор

**Polяnka**  
💬 Телеграм: `@polly_8b`  
📧 Email: `kadzuta56@gmail.com`
