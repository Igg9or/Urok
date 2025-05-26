import sqlite3
import json

DB = 'database.db'
JSON_FILE = 'templates.json'

with open(JSON_FILE, encoding='utf-8') as f:
    templates = json.load(f)

conn = sqlite3.connect(DB)
cursor = conn.cursor()

success_count = 0
error_count = 0

for tpl in templates:
    try:
        # Проверяем наличие обязательных полей
        if not all(key in tpl for key in ['textbook_id', 'name', 'question_template', 'answer_template', 'parameters']):
            print(f"⚠️ Пропущен шаблон с ошибкой структуры: {tpl.get('name', 'Без названия')}")
            error_count += 1
            continue
        
        # Пытаемся вставить или обновить запись
        cursor.execute('''
            INSERT INTO task_templates 
            (textbook_id, name, question_template, answer_template, parameters)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(textbook_id, name) DO UPDATE SET
                question_template = excluded.question_template,
                answer_template = excluded.answer_template,
                parameters = excluded.parameters
        ''', (
            tpl['textbook_id'],
            tpl['name'],
            tpl['question_template'],
            tpl['answer_template'],
            json.dumps(tpl['parameters'])
        ))
        success_count += 1
    except Exception as e:
        print(f"❌ Ошибка при обработке шаблона '{tpl.get('name', 'Без названия')}': {str(e)}")
        error_count += 1
        conn.rollback()
    else:
        conn.commit()

conn.close()

print(f"\nИтог:")
print(f"✅ Успешно обработано: {success_count}")
print(f"⚠️ С ошибками: {error_count}")
if error_count == 0:
    print("🎉 Все шаблоны успешно добавлены/обновлены в базе данных.")
else:
    print("Некоторые шаблоны не были обработаны. Проверьте вывод выше.")