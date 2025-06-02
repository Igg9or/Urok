from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os, re, json, random
import datetime
from datetime import datetime as dt
from math_engine import MathEngine
from task_generator import TaskGenerator

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Конфигурация БД
DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(task_templates)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'conditions' not in columns:
        cursor.execute('''
            ALTER TABLE task_templates
            ADD COLUMN conditions TEXT
        ''')

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
            answer TEXT NOT NULL,
            template_id INTEGER REFERENCES task_templates(id)
        )
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

    # Создаем таблицу учебников
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS textbooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            grade INTEGER NOT NULL,
            UNIQUE(title, grade))
    ''')

    # Создаем таблицу шаблонов заданий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            textbook_id INTEGER REFERENCES textbooks(id),
            name TEXT NOT NULL,
            question_template TEXT NOT NULL,
            answer_template TEXT NOT NULL,
            parameters TEXT NOT NULL,
            conditions TEXT,  
            answer_type TEXT DEFAULT 'numeric',  
            UNIQUE(textbook_id, name))
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lesson_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        question_template TEXT NOT NULL,
        answer_template TEXT NOT NULL,
        parameters TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')


    # В функции init_db(), после создания таблиц:
    cursor.execute("SELECT COUNT(*) FROM textbooks")
    if cursor.fetchone()[0] == 0:
        # Добавляем тестовые учебники
        textbooks = [
            ('Макарычев', 'Алгебра для 5 класса', 5),
            ('Мордкович', 'Алгебра для 7-9 классов', 7),
            ('Атанасян', 'Геометрия 7-9 классы', 7)
        ]
        
        for title, description, grade in textbooks:
            cursor.execute(
                "INSERT INTO textbooks (title, description, grade) VALUES (?, ?, ?)",
                (title, description, grade)
            )
        
        conn.commit()
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
            
            # Тестовый учебник
            cursor.execute(
                "INSERT INTO textbooks (title, description, grade) VALUES (?, ?, ?)",
                ('Макарычев', 'Алгебра для 5 класса', 5)
            )
            
            # Базовые шаблоны для учебника
            templates = [
                ('Сложение', '{A} + {B} = ?', '{A} + {B}', '{"A": {"min": 1, "max": 10}, "B": {"min": 1, "max": 10}}'),
                ('Вычитание', '{A} - {B} = ?', '{A} - {B}', '{"A": {"min": 1, "max": 20}, "B": {"min": 1, "max": 10}}'),
                ('Умножение', '{A} × {B} = ?', '{A} * {B}', '{"A": {"min": 1, "max": 10}, "B": {"min": 1, "max": 10}}'),
                ('Деление', '{A} ÷ {B} = ?', '{A} / {B}', '{"A": {"min": 1, "max": 50}, "B": {"min": 1, "max": 10}}'),
                ('Уравнение', 'Решите: {A}x + {B} = {C}', '({C} - {B}) / {A}', '{"A": {"min": 1, "max": 5}, "B": {"min": 1, "max": 20}, "C": {"min": 10, "max": 50}}')
            ]
            
            for name, question, answer, params in templates:
                cursor.execute(
                    "INSERT INTO task_templates (textbook_id, name, question_template, answer_template, parameters) VALUES (1, ?, ?, ?, ?)",
                    (name, question, answer, params)
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
    try:
        # Получаем информацию об уроке
        lesson = conn.execute('''
            SELECT l.id, l.title, l.date, c.grade, c.letter 
            FROM lessons l
            JOIN classes c ON l.class_id = c.id
            WHERE l.id = ? AND l.teacher_id = ?
        ''', (lesson_id, session['user_id'])).fetchone()
        
        if not lesson:
            return redirect(url_for('teacher_dashboard'))
        
        # Получаем задания урока
        tasks = conn.execute('''
            SELECT id, question, answer FROM lesson_tasks 
            WHERE lesson_id = ?
        ''', (lesson_id,)).fetchall()
        
        # Получаем все учебники и шаблоны уроков
        textbooks = conn.execute('SELECT * FROM textbooks ORDER BY grade, title').fetchall()
        lesson_templates = conn.execute('SELECT * FROM lesson_templates').fetchall()
        
        return render_template('edit_lesson.html',
                            lesson=dict(lesson),
                            tasks=[dict(task) for task in tasks],
                            textbooks=textbooks,
                            lesson_templates=lesson_templates)
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
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        for task in data['tasks']:
            if task['id']:
                cursor.execute('''
                    UPDATE lesson_tasks 
                    SET question = ?, answer = ?, template_id = ?
                    WHERE id = ? AND lesson_id = ?
                ''', (
                    task['question'], 
                    task['answer'],
                    task.get('template_id'),  # Новое поле
                    task['id'], 
                    lesson_id
                ))
            else:
                cursor.execute('''
                    INSERT INTO lesson_tasks 
                    (lesson_id, question, answer, template_id)
                    VALUES (?, ?, ?, ?)
                ''', (
                    lesson_id, 
                    task['question'], 
                    task['answer'],
                    task.get('template_id')  # Новое поле
                ))
                task['id'] = cursor.lastrowid
        
        conn.commit()
        return jsonify({'success': True, 'tasks': data['tasks']})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})

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
        # Проверка доступа для ученика
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
        
        if not lesson:
            return redirect(url_for('student_lessons'))
        
        # Получаем задания урока
        cursor.execute('''
            SELECT id, question, answer, template_id 
            FROM lesson_tasks
            WHERE lesson_id = ?
            ORDER BY id
        ''', (lesson_id,))
        base_tasks = cursor.fetchall()
        
        tasks = []
        
        for task in base_tasks:
            # Проверяем сохраненный вариант
            cursor.execute('''
                SELECT variant_data FROM student_task_variants
                WHERE lesson_id = ? AND user_id = ? AND task_id = ?
            ''', (lesson_id, user_id, task['id']))
            variant = cursor.fetchone()
            
            if variant:
                variant_data = json.loads(variant['variant_data'])
                question = task['question']
                answer_template = task['answer']
                
                # Подставляем параметры
                for param, value in variant_data['params'].items():
                    question = question.replace(f'{{{param}}}', str(value))
                
                try:
                    computed_answer = str(eval(answer_template.format(**variant_data['params'])))
                except:
                    computed_answer = answer_template.format(**variant_data['params'])
                
                tasks.append({
                    'id': task['id'],
                    'question': question,
                    'correct_answer': computed_answer,
                    'params': variant_data['params']
                })
            else:
                # Генерация нового варианта
                params = {}
                question_template = task['question']
                answer_template = task['answer']
                
                # Получаем параметры из шаблона, если есть
                if task['template_id']:
                    cursor.execute('''
                        SELECT parameters, conditions 
                        FROM task_templates 
                        WHERE id = ?
                    ''', (task['template_id'],))
                    template = cursor.fetchone()
                    
                    if template:
                        try:
                            template_params = json.loads(template['parameters'])
                            params = MathEngine.generate_parameters(template_params)
                            
                            # Обработка условий шаблона
                            if template['conditions']:
                                try:
                                    # Создаем безопасный контекст для exec
                                    exec_globals = {}
                                    exec_globals.update(params)
                                    exec(template['conditions'], exec_globals, {})
                                    params.update({k: v for k, v in exec_globals.items() 
                                                 if k not in ['__builtins__']})
                                except Exception as e:
                                    print(f"Error executing conditions: {e}")
                                    params = MathEngine.generate_parameters(template_params)
                        except json.JSONDecodeError:
                            print("Error decoding template parameters")
                            params = {}
                
                # Если параметров нет - генерируем случайные
                if not params:
                    param_matches = set(re.findall(r'\{([A-Za-z]+)\}', question_template))
                    for param in param_matches:
                        params[param] = random.randint(1, 10)
                
                # Формируем вопрос
                generated_question = question_template
                for param, value in params.items():
                    generated_question = generated_question.replace(f'{{{param}}}', str(value))
                
                # Вычисляем ответ
                try:
                    safe_dict = {f'_{k}': v for k, v in params.items()}
                    computed_answer = answer_template.format(**safe_dict)
                except Exception as e:
                    print(f"Error formatting answer: {e}")
                    computed_answer = "Ошибка в шаблоне ответа"
                
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
        print(f"Error in start_lesson: {str(e)}")
        return "Произошла ошибка при загрузке урока", 500
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
        # Получаем список учеников и их ответов
        cursor.execute('''
            SELECT 
                u.id as user_id, 
                u.full_name,
                t.id as task_id,
                sa.answer,
                sa.is_correct
            FROM users u
            JOIN lessons l ON u.class_id = l.class_id
            JOIN lesson_tasks t ON t.lesson_id = l.id
            LEFT JOIN student_answers sa ON sa.task_id = t.id AND sa.user_id = u.id
            WHERE l.id = ? AND u.role = 'student'
            ORDER BY u.full_name, t.id
        ''', (lesson_id,))
        
        # Формируем структуру результатов
        results = {}
        for row in cursor.fetchall():
            user_id = row['user_id']
            if user_id not in results:
                results[user_id] = {
                    'user_id': user_id,
                    'full_name': row['full_name'],
                    'tasks': []
                }
            
            results[user_id]['tasks'].append({
                'task_id': row['task_id'],
                'answered': row['answer'] is not None,
                'is_correct': row['is_correct'] if row['is_correct'] is not None else False
            })
        
        return jsonify({
            'results': list(results.values())
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



@app.route('/teacher/end_lesson/<int:lesson_id>', methods=['POST'])
def end_lesson(lesson_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Здесь можно добавить логику завершения урока
    # Например, пометить урок как завершенный в базе данных
    
    return jsonify({'success': True})


@app.route('/teacher/get_student_progress/<int:lesson_id>/<int:student_id>')
def get_student_progress(lesson_id, student_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Получаем прогресс конкретного ученика
        cursor.execute('''
            SELECT 
                t.id as task_id,
                sa.answer,
                sa.is_correct,
                sa.answered_at
            FROM lesson_tasks t
            LEFT JOIN student_answers sa ON sa.task_id = t.id AND sa.user_id = ?
            WHERE t.lesson_id = ?
            ORDER BY t.id
        ''', (student_id, lesson_id))
        
        tasks = []
        correct_count = 0
        
        for task in cursor.fetchall():
            if task['is_correct']:
                correct_count += 1
            tasks.append({
                'task_id': task['task_id'],
                'answered': task['answer'] is not None,
                'is_correct': task['is_correct'],
                'answered_at': task['answered_at']
            })
        
        total_tasks = len(tasks)
        progress = round((correct_count / total_tasks) * 100) if total_tasks > 0 else 0
        
        return jsonify({
            'student_id': student_id,
            'progress': progress,
            'tasks': tasks
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/teacher/manage_tasks')
def manage_tasks():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db()
    try:
        textbooks = conn.execute('SELECT * FROM textbooks ORDER BY grade, title').fetchall()
        return render_template('manage_tasks.html', 
                            full_name=session['full_name'],
                            textbooks=textbooks)
    except Exception as e:
        print(f"Error fetching textbooks: {e}")
        return "Произошла ошибка при загрузке учебников", 500
    finally:
        conn.close()


@app.route('/teacher/manage_tasks/<int:textbook_id>')
def textbook_tasks(textbook_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db()
    try:
        # Получаем учебник
        textbook = conn.execute('SELECT * FROM textbooks WHERE id = ?', (textbook_id,)).fetchone()
        if not textbook:
            flash('Учебник не найден', 'error')
            return redirect(url_for('manage_tasks'))
        
        # Получаем шаблоны заданий с нумерацией
        templates = conn.execute('''
            SELECT *, 
                   ROW_NUMBER() OVER (ORDER BY id) as task_number 
            FROM task_templates 
            WHERE textbook_id = ? 
            ORDER BY id
        ''', (textbook_id,)).fetchall()
        
        return render_template('textbook_tasks.html', 
                            full_name=session['full_name'],
                            textbook=dict(textbook),
                            templates=templates)
    except Exception as e:
        print(f"Error loading textbook tasks: {e}")
        flash('Произошла ошибка при загрузке заданий', 'error')
        return redirect(url_for('manage_tasks'))
    finally:
        conn.close()

@app.route('/teacher/add_task_template', methods=['POST'])
def add_task_template():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO task_templates 
            (textbook_id, name, question_template, answer_template, parameters)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['textbook_id'],
            data['name'],
            data['question_template'],
            data['answer_template'],
            json.dumps(data['parameters'])
        ))
        
        conn.commit()
        return jsonify({
            'success': True,
            'template_id': cursor.lastrowid
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/teacher/update_task_template/<int:template_id>', methods=['POST'])
def update_task_template(template_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE task_templates SET
                name = ?,
                question_template = ?,
                answer_template = ?,
                parameters = ?
            WHERE id = ?
        ''', (
            data['name'],
            data['question_template'],
            data['answer_template'],
            json.dumps(data['parameters']),
            template_id
        ))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/teacher/delete_task_template/<int:template_id>', methods=['DELETE'])
def delete_task_template(template_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM task_templates WHERE id = ?', (template_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()
        

@app.route('/teacher/add_textbook', methods=['POST'])
def add_textbook():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    grade = data.get('grade')
    
    if not title or not grade:
        return jsonify({'success': False, 'error': 'Название и класс обязательны'})
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO textbooks (title, description, grade)
            VALUES (?, ?, ?)
        ''', (title, description, grade))
        
        conn.commit()
        return jsonify({
            'success': True,
            'textbook_id': cursor.lastrowid
        })
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Учебник с таким названием и классом уже существует'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

# Маршрут для сохранения шаблона
@app.route('/api/templates', methods=['POST'])
def save_template():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    required_fields = ['textbook_id', 'name', 'question', 'answer', 'parameters']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db()
    try:
        # Проверяем, существует ли учебник
        textbook = conn.execute(
            'SELECT 1 FROM textbooks WHERE id = ?', 
            (data['textbook_id'],)
        ).fetchone()
        
        if not textbook:
            return jsonify({'error': 'Textbook not found'}), 404

        # Сохраняем шаблон
        conn.execute('''
            INSERT INTO task_templates 
            (textbook_id, name, question_template, answer_template, parameters)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['textbook_id'],
            data['name'],
            data['question'],
            data['answer'],
            json.dumps(data['parameters'])
        ))
        
        conn.commit()
        return jsonify({
            'success': True,
            'template_id': conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        })
    except sqlite3.IntegrityError as e:
        return jsonify({
            'success': False,
            'error': 'Template with this name already exists'
        }), 400
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        conn.close()

def get_textbook_templates(textbook_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    try:
        templates = conn.execute('''
            SELECT * FROM task_templates WHERE textbook_id = ?
        ''', (textbook_id,)).fetchall()
        
        return jsonify({
            'success': True,
            'templates': [dict(t) for t in templates]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
        
@app.route('/api/textbooks/<int:textbook_id>/templates')
def get_templates(textbook_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    try:
        templates = conn.execute('''
            SELECT id, name, question_template, answer_template, parameters
            FROM task_templates
            WHERE textbook_id = ?
            ORDER BY name
        ''', (textbook_id,)).fetchall()
        
        return jsonify({
            'success': True,
            'templates': [dict(t) for t in templates]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        conn.close()

# Маршрут для удаления шаблона
@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_templates(template_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    try:
        result = conn.execute(
            'DELETE FROM task_templates WHERE id = ?', 
            (template_id,)
        )
        conn.commit()
        
        if result.rowcount == 0:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
            
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/templates/<int:template_id>')
def get_template(template_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    try:
        template = conn.execute('''
            SELECT id, textbook_id, name, question_template, answer_template, parameters
            FROM task_templates
            WHERE id = ?
        ''', (template_id,)).fetchone()

        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404

        return jsonify({
            'success': True,
            'template': dict(template)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/generate_task', methods=['POST'])
def generate_task():
    data = request.get_json()
    template_id = data.get('template_id')
    
    conn = get_db()
    template = conn.execute('SELECT * FROM task_templates WHERE id = ?', [template_id]).fetchone()
    if not template:
        return jsonify({"error": "Template not found"}), 404

    params = json.loads(template['parameters'])
    generated_params = MathEngine.generate_parameters(params)
    
    question = template['question_template'].format(**generated_params)
    answer = MathEngine.evaluate_expression(template['answer_template'], generated_params)
    
    return jsonify({
        "question": question,
        "answer": answer,
        "params": generated_params
    })

@app.route('/api/check_answer', methods=['POST'])
def api_check_answer():
    try:
        data = request.get_json()
        print("Received data:", data)  # Логирование входящих данных
        
        if not data or 'answer' not in data or 'correct_answer' not in data:
            return jsonify({"error": "Invalid request data"}), 400
            
        user_answer = data.get('answer')
        correct_answer = data.get('correct_answer')
        params = data.get('params', {})
        
        # Сравниваем математически, а не как строки
        user_val = MathEngine.evaluate_expression(user_answer, params)
        correct_val = MathEngine.evaluate_expression(correct_answer, params)
        
        print("User value:", user_val, "Correct value:", correct_val)  # Логирование вычислений
        
        return jsonify({
            "is_correct": abs(float(user_val) - float(correct_val)) < 1e-6,
            "evaluated_answer": user_val
        })
    except Exception as e:
        print("Error in check_answer:", str(e))  # Логирование ошибок
        return jsonify({"error": str(e)}), 500
    
# В app.py добавить новый маршрут
@app.route('/api/generate_from_template/<int:template_id>')
def generate_from_template(template_id):
    conn = get_db()
    try:
        template = conn.execute('SELECT * FROM task_templates WHERE id = ?', [template_id]).fetchone()
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        template_dict = dict(template)
        template_dict['parameters'] = json.loads(template['parameters'])
        
        variant = TaskGenerator.generate_task_variant(template_dict)
        return jsonify(variant)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# В app.py добавляем новые маршруты и изменяем существующие

@app.route('/teacher/lesson_templates')
def manage_lesson_templates():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db()
    try:
        # Получаем все учебники для выбора шаблонов
        textbooks = conn.execute('SELECT * FROM textbooks ORDER BY grade, title').fetchall()
        return render_template('lesson_templates.html',
                            full_name=session['full_name'],
                            textbooks=textbooks)
    except Exception as e:
        print(f"Error: {e}")
        return "Произошла ошибка", 500
    finally:
        conn.close()

@app.route('/api/lesson_templates', methods=['POST'])
def save_lesson_template():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    required_fields = ['name', 'question_template', 'answer_template', 'parameters']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db()
    try:
        # Сохраняем шаблон для урока (без привязки к учебнику)
        conn.execute('''
            INSERT INTO lesson_templates 
            (name, question_template, answer_template, parameters)
            VALUES (?, ?, ?, ?)
        ''', (
            data['name'],
            data['question_template'],
            data['answer_template'],
            json.dumps(data['parameters'])
        ))
        
        conn.commit()
        return jsonify({
            'success': True,
            'template_id': conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        })
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/lesson_templates/<int:template_id>')
def get_lesson_template(template_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    try:
        template = conn.execute('''
            SELECT * FROM lesson_templates WHERE id = ?
        ''', (template_id,)).fetchone()

        if not template:
            return jsonify({'error': 'Template not found'}), 404

        return jsonify({
            'success': True,
            'template': dict(template)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/teacher/bulk_delete_templates', methods=['POST'])
def bulk_delete_templates():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    textbook_id = data['textbook_id']
    template_ids = data['template_ids']
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Удаляем только шаблоны, принадлежащие указанному учебнику
        placeholders = ','.join(['?'] * len(template_ids))
        cursor.execute(f'''
            DELETE FROM task_templates 
            WHERE id IN ({placeholders}) AND textbook_id = ?
        ''', (*template_ids, textbook_id))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        conn.close()
                
               
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)