import sqlite3
import json
from pathlib import Path

DB_PATH = 'database.db'
JSON_FILE = 'templates.json'

def import_templates():
    if not Path(JSON_FILE).exists():
        print(f"❌ Файл {JSON_FILE} не найден")
        return

    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            templates = json.load(f)
            
            # Если передан один шаблон (старый формат), оборачиваем в список
            if isinstance(templates, dict):
                templates = [templates]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        imported_count = 0
        
        for template in templates:
            try:
                # Подготовка данных для вставки
                textbook_id = template['textbook_id']
                name = template['name']
                question = template['question_template']
                answer = template['answer_template']
                
                # Сериализация параметров и валидации
                params = json.dumps(template.get('parameters', {}), ensure_ascii=False)
                validation = json.dumps(template.get('validation', {}), ensure_ascii=False)

                cursor.execute('''
                    INSERT INTO task_templates 
                    (textbook_id, name, question_template, answer_template, parameters, conditions)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (textbook_id, name, question, answer, params, validation))
                
                imported_count += 1
                print(f"✅ Добавлен шаблон: {name}")
                
            except KeyError as e:
                print(f"❌ Отсутствует обязательное поле {e} в шаблоне")
            except Exception as e:
                print(f"❌ Ошибка при импорте шаблона: {str(e)}")
                conn.rollback()

        conn.commit()
        print(f"\n✅ Импорт завершен. Успешно добавлено {imported_count} шаблонов")
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в формате JSON: {str(e)}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    import_templates()