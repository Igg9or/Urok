import sqlite3
import json
from pathlib import Path

DB_PATH = 'database.db'
JSON_FILE = 'templates.json'

def validate_template(template):
    """Проверяет шаблон на корректность перед импортом"""
    required_fields = ['textbook_id', 'name', 'question_template', 'answer_template', 'parameters']
    for field in required_fields:
        if field not in template:
            raise ValueError(f"Шаблон должен содержать поле '{field}'")
    
    # Проверка параметров
    for param, config in template['parameters'].items():
        if not isinstance(config, dict):
            raise ValueError(f"Параметр {param} должен быть словарем с настройками")
        
        if 'min' in config and 'max' in config and config['min'] > config['max']:
            raise ValueError(f"Для параметра {param} min не может быть больше max")

def import_templates():
    """Импортирует шаблоны из JSON в базу данных"""
    if not Path(JSON_FILE).exists():
        print(f"❌ Файл {JSON_FILE} не найден")
        return
    
    with open(JSON_FILE, encoding='utf-8') as f:
        templates = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем существование учебника
    textbook_ids = {t['textbook_id'] for t in templates}
    for textbook_id in textbook_ids:
        cursor.execute("SELECT 1 FROM textbooks WHERE id = ?", (textbook_id,))
        if not cursor.fetchone():
            print(f"❌ Учебник с ID {textbook_id} не существует")
            conn.close()
            return
    
    # Импортируем шаблоны
    imported_count = 0
    for tpl in templates:
        try:
            validate_template(tpl)
            
            # Проверяем, существует ли уже такой шаблон
            cursor.execute('''
                SELECT 1 FROM task_templates 
                WHERE textbook_id = ? AND name = ?
            ''', (tpl['textbook_id'], tpl['name']))
            
            if cursor.fetchone():
                print(f"⚠ Шаблон '{tpl['name']}' уже существует, пропускаем")
                continue
                
            cursor.execute('''
                INSERT INTO task_templates 
                (textbook_id, name, question_template, answer_template, parameters)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                tpl['textbook_id'],
                tpl['name'],
                tpl['question_template'],
                tpl['answer_template'],
                json.dumps(tpl['parameters'])
            ))
            imported_count += 1
            print(f"✅ Добавлен шаблон: '{tpl['name']}'")
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении шаблона '{tpl.get('name', '')}': {str(e)}")
            conn.rollback()
    
    conn.commit()
    conn.close()
    print(f"\n🎉 Импортировано {imported_count} шаблонов из {len(templates)}")

if __name__ == "__main__":
    import_templates()