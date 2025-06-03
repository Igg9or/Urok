import sqlite3
from app import DATABASE

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Добавляем новый столбец template_id
        cursor.execute("PRAGMA table_info(lesson_tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'answer_type' not in columns:
    print("Добавляем столбец answer_type в task_templates...")
    cursor.execute('''
        ALTER TABLE task_templates
        ADD COLUMN answer_type TEXT DEFAULT 'numeric'
    ''')
        if 'template_id' not in columns:
            print("Добавляем столбец template_id в lesson_tasks...")
            cursor.execute('''
                ALTER TABLE lesson_tasks
                ADD COLUMN template_id INTEGER REFERENCES task_templates(id)
            ''')
            conn.commit()
            print("Миграция успешно выполнена!")
        else:
            print("Структура БД уже актуальна")
            
    except Exception as e:
        print(f"Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()