diff --git a/migrate_db.py b/migrate_db.py
index 9a3d16d62c392c34c163c5260f7f3b00b9586ba8..11c4f6e8f7292874e476704b06b15862779afb00 100644
--- a/migrate_db.py
+++ b/migrate_db.py
@@ -1,31 +1,43 @@
 import sqlite3
 from app import DATABASE
 
 def migrate():
     conn = sqlite3.connect(DATABASE)
     cursor = conn.cursor()
     
     try:
-        # Добавляем новый столбец template_id
+        # Проверяем наличие столбца answer_type в task_templates
+        cursor.execute("PRAGMA table_info(task_templates)")
+        template_columns = [col[1] for col in cursor.fetchall()]
+        if 'answer_type' not in template_columns:
+            print("Добавляем столбец answer_type в task_templates...")
+            cursor.execute(
+                "ALTER TABLE task_templates ADD COLUMN answer_type TEXT DEFAULT 'numeric'"
+            )
+            conn.commit()
+
+        # Добавляем новый столбец template_id в lesson_tasks
         cursor.execute("PRAGMA table_info(lesson_tasks)")
         columns = [col[1] for col in cursor.fetchall()]
-        
+
         if 'template_id' not in columns:
             print("Добавляем столбец template_id в lesson_tasks...")
-            cursor.execute('''
+            cursor.execute(
+                """
                 ALTER TABLE lesson_tasks
                 ADD COLUMN template_id INTEGER REFERENCES task_templates(id)
-            ''')
+                """
+            )
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
\ No newline at end of file
