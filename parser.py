import json
import pandas as pd

with open('result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

my_name = "Polяnka"

all_my_messages = []

# Обходим каждый чат
for chat in data.get('chats', {}).get('list', []):
    last_received_message = None  # Для хранения последнего полученного сообщения

    for msg in chat.get('messages', []):
        if isinstance(msg.get('text'), str):  # Только текстовые сообщения
            sender = msg.get('from')
            message_text = msg.get('text')

            if sender != my_name and message_text:  # Если сообщение от другого человека
                # Запоминаем сообщение от другого человека
                last_received_message = {
                    'chat': chat.get('name'),
                    'date': msg.get('date'),
                    'text': message_text,
                    'target': None  # Это не наш ответ, это сообщение от другого человека
                }

            elif sender == my_name and last_received_message:  # Если это наше сообщение, и мы нашли предыдущее от другого человека
                # Добавляем ответ в список
                all_my_messages.append({
                    'chat': chat.get('name'),
                    'date': msg.get('date'),
                    'text': last_received_message['text'],  # Текст полученного сообщения
                    'target': message_text  # Наш ответ
                })
                last_received_message = None  # После ответа, сбрасываем

# Конвертируем собранные данные в DataFrame
df = pd.DataFrame(all_my_messages)
df.to_csv('my_messages.csv', index=False)
print(df.head())
