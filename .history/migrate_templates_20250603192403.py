import sqlite3
import re

DB_PATH = 'database.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, answer_template FROM task_templates")
rows = cursor.fetchall()

updated = 0

for template_id, answer_template in rows:
    original = answer_template.strip()

    # Проверяем, есть ли уже хотя бы одна пара фигурных скобок
    if re.search(r'\{.+?\}', original):
        continue

    # Проверяем, содержит ли выражение математические операторы и не является просто числом
    if any(op in original for op in '+-*/%()') and not original.isdigit():
        # Оборачиваем всё выражение в фигурные скобки
        new_template = '{' + original + '}'

        # Обновляем только если изменилось
        if new_template != original:
            cursor.execute(
                "UPDATE task_templates SET answer_template = ? WHERE id = ?",
                (new_template, template_id)
            )
            updated += 1

conn.commit()
conn.close()

print(f'✅ Обновлено {updated} шаблонов.')
