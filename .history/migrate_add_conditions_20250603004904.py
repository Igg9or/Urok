import sqlite3

DATABASE = 'database.db'

def migrate():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли столбец conditions
        cursor.execute("PRAGMA table_info(task_templates)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'conditions' not in columns:
            print("Добавляем столбец conditions в task_templates...")
            cursor.execute('''
                ALTER TABLE task_templates
                ADD COLUMN conditions TEXT
            ''')
            conn.commit()
            print("Миграция успешно выполнена!")
        else:
            print("Столбец conditions уже существует")
            
    except Exception as e:
        print(f"Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()