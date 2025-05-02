from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat"
DEEPSEEK_API_KEY = "sk-0eebbaabbab648099f7e507d6e30f03a"  # Замените на реальный ключ
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
        grade INTEGER,
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
        params TEXT NOT NULL,  -- JSON: список параметров ["A", "B"]
        FOREIGN KEY (lesson_id) REFERENCES lessons(id)
    )
    
    
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

@app.route('/teacher/create_lesson', methods=['POST'])
def create_lesson():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    template = data['template']
    params = data['params']
    
    # Генерация ответов для разных вариантов (простая версия)
    if "x + {B} = {C}" in template:
        answer_logic = "x = (C - B)/A"
    elif "x² + {B}x + {C} = 0" in template:
        answer_logic = "x1=(-B+sqrt(B^2-4*A*C))/(2*A); x2=(-B-sqrt(B^2-4*A*C))/(2*A)"
    else:
        # Общий случай для простых арифметических выражений
        answer_logic = "eval(expression)"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO lessons (teacher_id, grade, template, params, answer_logic)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        session['user_id'],
        data['grade'],
        template,
        json.dumps(params),
        answer_logic
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})
# Добавляем новые маршруты
@app.route('/teacher/create_lesson/<class_name>')
def create_lesson(class_name):
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('login'))
    return render_template('teacher_create_lesson.html', class_name=class_name)

@app.route('/teacher/generate_with_ai', methods=['POST'])
def generate_with_ai():
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    # Интеграция с DeepSeek API
    try:
        response = requests.post(
            'https://api.deepseek.com/v1/chat',
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'math-specialist',
                'messages': [{
                    'role': 'user',
                    'content': f"Сгенерируй 3 математических задания для школы. {prompt} Используй параметры в фигурных скобках {{A}}, {{B}}."
                }]
            }
        )
        
        # Парсинг ответа (упрощённо)
        ai_response = response.json()
        tasks = parse_ai_tasks(ai_response['choices'][0]['message']['content'])
        
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/teacher/save_lesson', methods=['POST'])
def save_lesson():
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Сохраняем урок
        cursor.execute('''
            INSERT INTO lessons (teacher_id, class_name, created_at)
            VALUES (?, ?, datetime('now'))
        ''', (session['user_id'], data['class_name']))
        lesson_id = cursor.lastrowid
        
        # Сохраняем задания
        for task in data['tasks']:
            cursor.execute('''
                INSERT INTO tasks (lesson_id, template, params)
                VALUES (?, ?, ?)
            ''', (lesson_id, task['text'], json.dumps(task['params'])))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()


def parse_ai_response(response_text):
    """Парсинг ответа от DeepSeek для извлечения заданий"""
    tasks = []
    # Простейший парсинг (можно улучшить под ваш формат)
    for line in response_text.split('\n'):
        if '{' in line and '}' in line:
            tasks.append(line.strip())
    return tasks[:3]  # Берем первые 3 задания

@app.route('/teacher/generate_with_ai', methods=['POST'])
def generate_with_ai():
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
                    "content": f"""Сгенерируй математические задания по следующему описанию:
                    {prompt}
                    Требования:
                    1. Используй параметры в фигурных скобках (например: {{A}}, {{B}})
                    2. Формат: одно задание на строку
                    3. Только математика для школы"""
                }]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            tasks = parse_ai_response(response.json()['choices'][0]['message']['content'])
            return jsonify({"success": True, "tasks": tasks})
        else:
            return jsonify({"success": False, "error": "API error"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    





with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)