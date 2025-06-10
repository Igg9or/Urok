import sqlite3
import json

DB_PATH = 'database.db'
JSON_FILE = 'templates.json'

with open(JSON_FILE, encoding='utf-8') as f:
    templates = json.load(f)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for tpl in templates:
    cursor.execute('''
        INSERT OR REPLACE INTO task_templates
        (textbook_id, name, question_template, answer_template, parameters, conditions, answer_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        tpl['textbook_id'],
        tpl['name'],
        tpl['question_template'],
        tpl['answer_template'],
        json.dumps(tpl['parameters'], ensure_ascii=False),
        tpl.get('conditions'),
        tpl.get('answer_type', 'numeric')
    ))

conn.commit()
conn.close()

print("✅ Шаблоны успешно загружены в базу данных.")
