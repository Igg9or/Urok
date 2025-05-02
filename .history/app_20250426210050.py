from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import requests
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
CORS(app)

# Конфигурация
DATABASE = 'database.db'
DEEPSEEK_API_KEY = 'your_deepseek_api_key_here'  # Замените на реальный ключ
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat'

# Инициализация БД
def init_db():
    with app.app_context():
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT
        )
        ''')
        
        # Таблица уроков
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES users(id)
        )
        ''')
        
        # Таблица заданий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            template TEXT NOT NULL,
            params TEXT NOT NULL,
            FOREIGN KEY (lesson_id) REFERENCES lessons(id)
        )
        ''')
        
        # Тестовые данные
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                ('teacher1', generate_password_hash('teacher123'), 'teacher', 'Иванов И.И.')
            )
            cursor.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                ('student1', generate_password_hash('student123'), 'student', 'Петров П.П.')
            )
        
        conn.commit()
        conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Маршруты аутентификации
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session.update({
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'full_name': user['full_name']
            })
            return redirect(url_for('dashboard'))
        
        return render_template('auth.html', error="Неверные данные")
    
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Основные маршруты
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    
    conn = get_db()
    lessons = conn.execute('''
        SELECT lessons.*, COUNT(tasks.id) as task_count 
        FROM lessons 
        LEFT JOIN tasks ON lessons.id = tasks.lesson_id
        WHERE teacher_id = ?
        GROUP BY lessons.id
        ORDER BY created_at DESC
        LIMIT 5
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('teacher_dashboard.html', 
                         full_name=session['full_name'],
                         recent_lessons=lessons)

@app.route('/teacher/lessons/new/<class_name>')
def create_lesson_page(class_name):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    return render_template('teacher_create_lesson.html', class_name=class_name)

# API для работы с заданиями
@app.route('/api/teacher/generate-tasks', methods=['POST'])
def generate_ai_tasks():
    try:
        prompt = request.json.get('prompt', '')
        
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "math-specialist",
                "messages": [{
                    "role": "user",
                    "content": f"Сгенерируй 3-5 математических заданий для школы. {prompt} Используй параметры в фигурных скобках: {{A}}, {{B}} и т.д. Формат: каждое задание на новой строке."
                }]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            tasks = [t.strip() for t in response.json()['choices'][0]['message']['content'].split('\n') if t.strip()]
            return jsonify({"success": True, "tasks": tasks})
        return jsonify({"success": False, "error": "API error"}), 500
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/teacher/save-lesson', methods=['POST'])
def save_lesson():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    data = request.get_json()
    class_name = data.get('class_name')
    tasks = data.get('tasks', [])
    
    if not class_name or not tasks:
        return jsonify({"success": False, "error": "Invalid data"}), 400
    
    conn = get_db()
    try:
        # Сохраняем урок
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lessons (teacher_id, class_name) VALUES (?, ?)",
            (session['user_id'], class_name)
        )
        lesson_id = cursor.lastrowid
        
        # Сохраняем задания
        for task in tasks:
            params = list(set([p.upper() for p in task['params']]))
            cursor.execute(
                "INSERT INTO tasks (lesson_id, template, params) VALUES (?, ?, ?)",
                (lesson_id, task['text'], ','.join(params))
            )
        
        conn.commit()
        return jsonify({"success": True, "lesson_id": lesson_id})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)