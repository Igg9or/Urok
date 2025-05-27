document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    const userId = document.querySelector('.task-card')?.dataset.userId;
    
    // 1. Загружаем задания с сервера
    loadTasks(lessonId, userId);
    
    // 2. Обработчики для проверки ответов
    document.querySelectorAll('.btn-check').forEach(btn => {
        btn.addEventListener('click', checkAnswer);
    });
});

// Загрузка заданий с сервера
async function loadTasks(lessonId, userId) {
    try {
        const response = await fetch('/api/verify_answer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (!response.ok) throw new Error('Ошибка сервера');
        
        const data = await response.json();
        
        if (data.success) {
            renderTasks(data.tasks);
        } else {
            alert('Ошибка: ' + (data.error || 'неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить задания');
    }
}

// Отображение заданий
function renderTasks(tasks) {
    const container = document.querySelector('.tasks-container');
    container.innerHTML = '';
    
    tasks.forEach((task, index) => {
        const taskHtml = `
            <div class="task-card" data-task-id="${task.id}">
                <div class="task-header">
                    <div class="task-number">Задание ${index + 1}</div>
                    <div class="task-status"></div>
                </div>
                <div class="task-body">
                    <div class="task-question">${task.question}</div>
                    <div class="task-answer">
                        <input type="text" class="answer-input" placeholder="Введите ответ">
                        <button class="btn btn-check">Проверить</button>
                    </div>
                    <div class="task-feedback hidden">
                        <div class="feedback-correct hidden">
                            <span class="icon">✓</span>
                            <span>Правильно!</span>
                        </div>
                        <div class="feedback-incorrect hidden">
                            <span class="icon">✗</span>
                            <span>Ошибка! Правильный ответ: ${task.correct_answer}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', taskHtml);
    });
}

// Проверка ответа
async function checkAnswer(event) {
    const taskCard = event.target.closest('.task-card');
    const taskId = taskCard.dataset.taskId;
    const userAnswer = taskCard.querySelector('.answer-input').value.trim();
    
    if (!userAnswer) {
        alert('Введите ответ');
        return;
    }
    
    try {
        const response = await fetch('/api/check_answer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                task_id: taskId,
                user_answer: userAnswer
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showFeedback(taskCard, result.is_correct, result.correct_answer);
        } else {
            alert('Ошибка: ' + (result.error || ''));
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка соединения');
    }
}

// Показать результат проверки
function showFeedback(taskCard, isCorrect, correctAnswer) {
    const feedback = taskCard.querySelector('.task-feedback');
    const status = taskCard.querySelector('.task-status');
    
    if (isCorrect) {
        taskCard.querySelector('.feedback-correct').classList.remove('hidden');
        status.style.backgroundColor = '#2ed573'; // Зелёный
    } else {
        taskCard.querySelector('.feedback-incorrect').classList.remove('hidden');
        taskCard.querySelector('.correct-answer').textContent = correctAnswer;
        status.style.backgroundColor = '#ff4757'; // Красный
    }
    
    feedback.classList.remove('hidden');
    taskCard.querySelector('.answer-input').disabled = true;
    event.target.disabled = true;
}