from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Конфигурация БД
DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Создаем таблицу пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,  -- 'student' или 'teacher'
        full_name TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER REFERENCES users(id),
        grade TEXT NOT NULL,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        template TEXT,
        params TEXT,  -- JSON с параметрами
        answer_logic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Создаем таблицу предметов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    )
    ''')
    
    # Проверяем, есть ли уже тестовые пользователи
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Добавляем тестовых пользователей
        cursor.execute("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                      ('teacher1', generate_password_hash('teacher123'), 'teacher', 'Иванов Иван Иванович'))
        cursor.execute("INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                      ('student1', generate_password_hash('student123'), 'student', 'Петров Петр'))
        
        # Добавляем тестовые предметы
        cursor.execute("INSERT INTO subjects (name, description) VALUES (?, ?)",
                      ('Математика', 'Алгебра и геометрия'))
    
    conn.commit()
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
    
    grade = request.args.get('grade')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, date FROM lessons 
        WHERE teacher_id = ? AND grade = ?
        ORDER BY date DESC
    ''', (session['user_id'], grade))
    lessons = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'lessons': [dict(lesson) for lesson in lessons]
    })

@app.route('/teacher/edit_lesson/<int:lesson_id>')
def edit_lesson(lesson_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    
    # Получаем основную информацию об уроке
    cursor.execute('''
        SELECT id, title, date, grade FROM lessons 
        WHERE id = ? AND teacher_id = ?
    ''', (lesson_id, session['user_id']))
    lesson = cursor.fetchone()
    
    if not lesson:
        return redirect(url_for('teacher_dashboard'))
    
    # Получаем задания для этого урока
    cursor.execute('''
        SELECT id, question, answer FROM lesson_tasks 
        WHERE lesson_id = ?
    ''', (lesson_id,))
    tasks = cursor.fetchall()
    
    conn.close()
    
    return render_template('edit_lesson.html', 
                        lesson=dict(lesson),
                        tasks=[dict(task) for task in tasks],
                        today_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/teacher/conduct_lesson/<int:lesson_id>')
def conduct_lesson(lesson_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    # Здесь будет логика для страницы проведения урока
    return render_template('conduct_lesson.html', lesson_id=lesson_id)

# Обновляем create_lesson
@app.route('/teacher/create_lesson', methods=['POST'])
def create_lesson():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO lessons (teacher_id, grade, title, date)
        VALUES (?, ?, ?, ?)
    ''', (
        session['user_id'],
        data['grade'],
        data['title'],
        data['date']
    ))
    lesson_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'lesson_id': lesson_id
    })

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

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)