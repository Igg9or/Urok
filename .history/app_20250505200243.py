from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os, re, json, random
import datetime
from datetime import datetime as dt

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Конфигурация БД
DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Создаем таблицу классов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade INTEGER NOT NULL,
            letter TEXT NOT NULL,
            UNIQUE(grade, letter))
    ''')

    # Создаем таблицу пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            class_id INTEGER REFERENCES classes(id),
            UNIQUE(username, class_id))
    ''')

    # Создаем таблицу уроков
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER REFERENCES users(id),
            class_id INTEGER REFERENCES classes(id),
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')

    # Создаем таблицу заданий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesson_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER REFERENCES lessons(id),
            question TEXT NOT NULL,
            answer TEXT NOT NULL)
    ''')

    # Создаем таблицу предметов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT)
    ''')

    # Создаем таблицу вариантов заданий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_task_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER REFERENCES lessons(id),
            user_id INTEGER REFERENCES users(id),
            task_id INTEGER REFERENCES lesson_tasks(id),
            variant_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lesson_id, user_id, task_id))
    ''')

    # Создаем таблицу ответов учеников
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_answers (
            task_id INTEGER REFERENCES lesson_tasks(id),
            user_id INTEGER REFERENCES users(id),
            answer TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (task_id, user_id))
    ''')

    # Добавляем тестовые данные
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Тестовые классы
            for grade in [5, 6, 7, 8, 9, 10, 11]:
                for letter in ['А', 'Б', 'В', 'Г']:
                    cursor.execute(
                        "INSERT OR IGNORE INTO classes (grade, letter) VALUES (?, ?)",
                        (grade, letter)
                    )
            
            # Тестовый учитель
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                ('teacher1', generate_password_hash('teacher123'), 'teacher', 'Иванова Мария Сергеевна')
            )
            
            # Тестовые ученики
            test_students = [
                ('student1', 'student123', '6В', 'Петров Петр'),
                ('student2', 'student123', '6В', 'Сидорова Анна'),
                ('student3', 'student123', '6Г', 'Кузнецов Алексей')
            ]
            
            for username, password, class_name, full_name in test_students:
                grade = int(class_name[:-1])
                letter = class_name[-1]
                
                # Получаем class_id перед использованием
                cursor.execute(
                    "SELECT id FROM classes WHERE grade = ? AND letter = ?",
                    (grade, letter)
                )
                class_row = cursor.fetchone()
                if class_row:
                    class_id = class_row[0]
                    
                    cursor.execute(
                        "INSERT INTO users (username, password, role, full_name, class_id) VALUES (?, ?, ?, ?, ?)",
                        (username, generate_password_hash(password), 'student', full_name, class_id)
                    )
            
            # Тестовый предмет
            cursor.execute(
                "INSERT INTO subjects (name, description) VALUES (?, ?)",
                ('Математика', 'Алгебра и геометрия 6 класс')
            )
            
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при инициализации БД: {e}")
    finally:
        conn.close()


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    if 'user_id' in session:
        if session['role'] == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('teacher_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('teacher_dashboard'))
        else:
            return render_template('auth.html', error="Неверное имя пользователя или пароль")
    
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()
    conn.close()
    
    return render_template('student_dashboard.html', 
                         full_name=session['full_name'],
                         subjects=subjects)

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    return render_template('teacher_dashboard.html', 
                         full_name=session['full_name'])


@app.route('/teacher/get_lessons')
def get_lessons():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    class_full = request.args.get('grade')  # Формат "6В"
    grade = class_full[:-1]  # "6"
    letter = class_full[-1]  # "В"
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Находим ID класса
        cursor.execute("SELECT id FROM classes WHERE grade = ? AND letter = ?", (grade, letter))
        class_id = cursor.fetchone()
        
        if not class_id:
            return jsonify({'lessons': []})
        
        # Получаем уроки для этого класса
        cursor.execute('''
            SELECT l.id, l.title, l.date 
            FROM lessons l
            WHERE l.class_id = ? AND l.teacher_id = ?
            ORDER BY l.date DESC
        ''', (class_id[0], session['user_id']))
        
        lessons = cursor.fetchall()
        return jsonify({
            'lessons': [dict(lesson) for lesson in lessons]
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/teacher/edit_lesson/<int:lesson_id>')
def edit_lesson(lesson_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Получаем урок с информацией о классе
        cursor.execute('''
            SELECT l.id, l.title, l.date, c.grade, c.letter 
            FROM lessons l
            JOIN classes c ON l.class_id = c.id
            WHERE l.id = ? AND l.teacher_id = ?
        ''', (lesson_id, session['user_id']))
        
        lesson = cursor.fetchone()
        if not lesson:
            return redirect(url_for('teacher_dashboard'))
        
        # Получаем задания
        cursor.execute('''
            SELECT id, question, answer FROM lesson_tasks 
            WHERE lesson_id = ?
        ''', (lesson_id,))
        tasks = cursor.fetchall()
        
        return render_template('edit_lesson.html',
                            lesson=dict(lesson),
                            tasks=[dict(task) for task in tasks])
    finally:
        conn.close()

@app.route('/teacher/conduct_lesson/<int:lesson_id>')
def conduct_lesson(lesson_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Получаем информацию об уроке
        cursor.execute('''
            SELECT l.id, l.title, l.date, c.grade, c.letter 
            FROM lessons l
            JOIN classes c ON l.class_id = c.id
            WHERE l.id = ? AND l.teacher_id = ?
        ''', (lesson_id, session['user_id']))
        
        lesson = cursor.fetchone()
        if not lesson:
            return redirect(url_for('teacher_dashboard'))
        
        # Получаем список учеников класса
        cursor.execute('''
            SELECT u.id, u.full_name
            FROM users u
            JOIN classes c ON u.class_id = c.id
            JOIN lessons l ON l.class_id = c.id
            WHERE l.id = ? AND u.role = 'student'
            ORDER BY u.full_name
        ''', (lesson_id,))
        students = cursor.fetchall()
        
        # Получаем задания урока
        cursor.execute('''
            SELECT id, question FROM lesson_tasks
            WHERE lesson_id = ?
            ORDER BY id
        ''', (lesson_id,))
        tasks = cursor.fetchall()
        
        return render_template('conduct_lesson.html',
                            lesson=dict(lesson),
                            students=students,
                            tasks=tasks)
    except Exception as e:
        print(f"Error: {e}")
        return "Произошла ошибка", 500
    finally:
        conn.close()

@app.route('/teacher/create_lesson', methods=['POST'])
def create_lesson():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    class_full = data['grade']  # Формат "6В"
    
    try:
        grade = int(class_full[:-1])  # "6"
        letter = class_full[-1]       # "В"
    except:
        return jsonify({'error': 'Invalid class format'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Находим ID класса
        cursor.execute("SELECT id FROM classes WHERE grade = ? AND letter = ?", (grade, letter))
        class_id = cursor.fetchone()
        
        if not class_id:
            return jsonify({'error': 'Class not found'}), 404
        
        # Создаем урок
        cursor.execute('''
            INSERT INTO lessons (teacher_id, class_id, title, date)
            VALUES (?, ?, ?, ?)
        ''', (
            session['user_id'],
            class_id[0],
            data['title'],
            data['date']
        ))
        
        lesson_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'success': True,
            'lesson_id': lesson_id
        })
    except Exception as e:
        conn.rollback()
        print(f"Error creating lesson: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/teacher/update_lesson/<int:lesson_id>', methods=['POST'])
def update_lesson(lesson_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Обновляем или добавляем задания
        updated_tasks = []
        for task in data['tasks']:
            if task['id']:
                # Обновление существующего задания
                cursor.execute('''
                    UPDATE lesson_tasks 
                    SET question = ?, answer = ?
                    WHERE id = ? AND lesson_id = ?
                ''', (task['question'], task['answer'], task['id'], lesson_id))
            else:
                # Добавление нового задания
                cursor.execute('''
                    INSERT INTO lesson_tasks (lesson_id, question, answer)
                    VALUES (?, ?, ?)
                ''', (lesson_id, task['question'], task['answer']))
                updated_tasks.append({'id': cursor.lastrowid})
        
        conn.commit()
        return jsonify({'success': True, 'tasks': updated_tasks})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/teacher/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверяем, что задание принадлежит учителю
        cursor.execute('''
            DELETE FROM lesson_tasks 
            WHERE id = ? AND lesson_id IN (
                SELECT id FROM lessons WHERE teacher_id = ?
            )
        ''', (task_id, session['user_id']))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/teacher/manage_students')
def manage_students():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classes ORDER BY grade, letter")
    classes = cursor.fetchall()
    conn.close()
    
    return render_template('manage_students.html', classes=classes)

@app.route('/teacher/get_students')
def get_students():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    class_id = request.args.get('class_id')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, full_name FROM users 
        WHERE role = 'student' AND class_id = ?
        ORDER BY full_name
    ''', (class_id,))
    students = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'students': [dict(student) for student in students]
    })

@app.route('/teacher/add_student', methods=['POST'])
def add_student():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password, role, full_name, class_id)
            VALUES (?, ?, 'student', ?, ?)
        ''', (
            data['username'],
            generate_password_hash(data['password']),
            data['full_name'],
            data['class_id']
        ))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError as e:
        return jsonify({'success': False, 'error': 'Логин уже существует'})
    finally:
        conn.close()

@app.route('/teacher/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ? AND role = 'student'", (student_id,))
        conn.commit()
        return jsonify({'success': cursor.rowcount > 0})
    finally:
        conn.close()


@app.route('/student/lessons')
def student_lessons():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Получаем класс ученика
        cursor.execute("SELECT class_id FROM users WHERE id = ?", (session['user_id'],))
        class_id = cursor.fetchone()
        
        if not class_id:
            return "У вас не указан класс", 400
        
        class_id = class_id[0]
        
        # Получаем уроки для этого класса
        cursor.execute('''
            SELECT l.id, l.title, l.date, u.full_name as teacher_name 
            FROM lessons l
            JOIN users u ON l.teacher_id = u.id
            WHERE l.class_id = ?
            ORDER BY l.date DESC
        ''', (class_id,))
        lessons = cursor.fetchall()
        
        return render_template('student_lessons.html', 
                            lessons=lessons,
                            full_name=session['full_name'])
    except Exception as e:
        print(f"Error: {e}")
        return "Произошла ошибка", 500
    finally:
        conn.close()


@app.route('/lesson/<int:lesson_id>')
def start_lesson(lesson_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверка доступа
        if session['role'] == 'student':
            cursor.execute('''
                SELECT 1 FROM lessons l
                JOIN users u ON l.class_id = u.class_id
                WHERE u.id = ? AND l.id = ?
            ''', (user_id, lesson_id))
            if not cursor.fetchone():
                return redirect(url_for('student_lessons'))
        
        # Получаем информацию об уроке
        cursor.execute('''
            SELECT l.title, l.date, u.full_name as teacher_name
            FROM lessons l
            JOIN users u ON l.teacher_id = u.id
            WHERE l.id = ?
        ''', (lesson_id,))
        lesson = cursor.fetchone()
        
        # Получаем базовые задания урока
        cursor.execute('''
            SELECT id, question, answer FROM lesson_tasks
            WHERE lesson_id = ?
            ORDER BY id
        ''', (lesson_id,))
        base_tasks = cursor.fetchall()
        
        tasks = []
        
        for task in base_tasks:
            # Проверяем, есть ли сохраненный вариант
            cursor.execute('''
                SELECT variant_data FROM student_task_variants
                WHERE lesson_id = ? AND user_id = ? AND task_id = ?
            ''', (lesson_id, user_id, task['id']))
            variant = cursor.fetchone()
            
            if variant:
                # Используем сохраненный вариант
                variant_data = json.loads(variant['variant_data'])
                question = task['question']
                answer = task['answer']
                
                # Заменяем параметры в вопросе
                for param, value in variant_data['params'].items():
                    question = question.replace(f'{{{param}}}', str(value))
                
                # Вычисляем ответ
                computed_answer = str(eval(answer.format(**variant_data['params'])))
                
                tasks.append({
                    'id': task['id'],
                    'question': question,
                    'correct_answer': computed_answer,
                    'params': variant_data['params']
                })
            else:
                # Генерируем новый вариант и сохраняем
                params = {}
                question = task['question']
                answer = task['answer']
                
                # Генерация параметров
                param_matches = set(re.findall(r'\{([A-Z])\}', question))
                for param in param_matches:
                    params[param] = random.randint(1, 10)  # Диапазон можно настроить
                
                # Заменяем параметры в вопросе
                generated_question = question
                for param, value in params.items():
                    generated_question = generated_question.replace(f'{{{param}}}', str(value))
                
                # Вычисляем ответ
                computed_answer = str(eval(answer.format(**params)))
                
                # Сохраняем вариант
                variant_data = {
                    'params': params,
                    'generated_question': generated_question,
                    'computed_answer': computed_answer
                }
                
                cursor.execute('''
                    INSERT INTO student_task_variants
                    (lesson_id, user_id, task_id, variant_data)
                    VALUES (?, ?, ?, ?)
                ''', (lesson_id, user_id, task['id'], json.dumps(variant_data)))
                
                tasks.append({
                    'id': task['id'],
                    'question': generated_question,
                    'correct_answer': computed_answer,
                    'params': params
                })
        
        conn.commit()
        return render_template('student_lesson.html',
                            lesson=dict(lesson),
                            tasks=tasks,
                            user_id=user_id)
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return "Произошла ошибка", 500
    finally:
        conn.close()

@app.route('/save_answer', methods=['POST'])
def save_answer():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO student_answers
            (task_id, user_id, answer, is_correct, answered_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            data['task_id'],
            data['user_id'],
            data['answer'],
            data['is_correct']
        ))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/check_answer', methods=['POST'])
def check_answer():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    user_id = session['user_id']
    task_id = data['task_id']
    lesson_id = data['lesson_id']
    user_answer = data['user_answer']
    correct_answer = data['correct_answer']
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Проверяем ответ (можно добавить более сложную логику)
        is_correct = str(user_answer) == str(correct_answer)
        
        # Сохраняем результат
        cursor.execute('''
            INSERT OR REPLACE INTO student_answers
            (task_id, user_id, answer, is_correct, answered_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (task_id, user_id, user_answer, is_correct))
        
        conn.commit()
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct_answer
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/teacher/get_lesson_results/<int:lesson_id>')
def get_lesson_results(lesson_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Получаем список учеников класса
        cursor.execute('''
            SELECT u.id, u.full_name
            FROM users u
            JOIN lessons l ON u.class_id = l.class_id
            WHERE l.id = ? AND u.role = 'student'
            ORDER BY u.full_name
        ''', (lesson_id,))
        students = cursor.fetchall()
        
        # Получаем список заданий урока
        cursor.execute('''
            SELECT id FROM lesson_tasks
            WHERE lesson_id = ?
            ORDER BY id
        ''', (lesson_id,))
        tasks = cursor.fetchall()
        
        # Собираем результаты
        results = []
        for student in students:
            student_result = {
                'user_id': student['id'],
                'full_name': student['full_name'],
                'tasks': []
            }
            
            for task in tasks:
                cursor.execute('''
                    SELECT answer, is_correct
                    FROM student_answers
                    WHERE task_id = ? AND user_id = ?
                ''', (task['id'], student['id']))
                answer = cursor.fetchone()
                
                student_result['tasks'].append({
                    'answered': answer is not None,
                    'is_correct': answer['is_correct'] if answer else False
                })
            
            results.append(student_result)
        
        return jsonify({
            'results': results,
            'total_tasks': len(tasks)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/get_student_answers/<int:lesson_id>/<int:user_id>')
def get_student_answers(lesson_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT sa.task_id, sa.answer, sa.is_correct
            FROM student_answers sa
            JOIN lesson_tasks lt ON sa.task_id = lt.id
            WHERE lt.lesson_id = ? AND sa.user_id = ?
        ''', (lesson_id, user_id))
        
        answers = cursor.fetchall()
        return jsonify([dict(answer) for answer in answers])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)