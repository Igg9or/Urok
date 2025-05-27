import sqlite3
import json
import os

# ✅ Имя файла базы данных
DB_PATH = 'database.db'

# ✅ Имя файла с шаблонами
JSON_FILE = 'templates.json'

# Проверим, существует ли база
if not os.path.exists(DB_PATH):
    print(f"❌ База данных {DB_PATH} не найдена!")
    exit()

# Загружаем шаблоны из файла
with open(JSON_FILE, encoding='utf-8') as f:
    templates = json.load(f)

# Подключаемся к базе
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Добавляем шаблоны
inserted = 0
for tpl in templates:
    try:
        cursor.execute('''
            INSERT INTO task_templates 
            (textbook_id, name, question_template, answer_template, parameters)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            tpl['textbook_id'],
            tpl['name'],
            tpl['question_template'],
            tpl['answer_template'],
            json.dumps(tpl['parameters'], ensure_ascii=False)
        ))
        inserted += 1
    except sqlite3.IntegrityError:
        print(f"⚠️ Шаблон уже существует: {tpl['name']}")
    except Exception as e:
        print(f"❌ Ошибка при добавлении шаблона {tpl['name']}: {e}")

conn.commit()
conn.close()

print(f"✅ Загружено новых шаблонов: {inserted}")
