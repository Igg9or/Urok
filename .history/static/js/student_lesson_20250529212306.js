document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    let completedTasks = 0;
    
    // Функция для отображения результата
    function showResult(taskCard, isCorrect, evaluatedAnswer = null) {
        const feedback = taskCard.querySelector('.task-feedback');
        const correctFeedback = taskCard.querySelector('.feedback-correct');
        const incorrectFeedback = taskCard.querySelector('.feedback-incorrect');
        const status = taskCard.querySelector('.task-status');
        
        if (isCorrect) {
            correctFeedback.classList.remove('hidden');
            incorrectFeedback.classList.add('hidden');
            status.style.backgroundColor = 'var(--success-color)';
            completedTasks++;
        } else {
            correctFeedback.classList.add('hidden');
            incorrectFeedback.classList.remove('hidden');
            if (evaluatedAnswer) {
                incorrectFeedback.querySelector('.user-answer').textContent = 
                    `Ваш ответ: ${evaluatedAnswer}`;
            }
            status.style.backgroundColor = 'var(--error-color)';
        }
        
        feedback.classList.remove('hidden');
        taskCard.querySelector('.answer-input').disabled = true;
        taskCard.querySelector('.btn-check').disabled = true;
        updateProgress();
    }
    
    // Новая функция проверки ответа через API
    async function checkAnswer(taskCard) {
    const taskId = taskCard.dataset.taskId;
    const userAnswer = taskCard.querySelector('.answer-input').value.trim();
    const correctAnswer = taskCard.querySelector('.correct-answer').textContent;
    const params = JSON.parse(taskCard.dataset.params || '{}');
    
    try {
        const response = await fetch('/api/check_answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: taskId,
                answer: userAnswer,
                correct_answer: correctAnswer,
                params: params
            })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка сервера');
        }
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        showResult(taskCard, result.is_correct, result.evaluated_answer);
        await saveAnswerToServer(taskId, userAnswer, result.is_correct);
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка при проверке ответа: ' + error.message);
    }
}
    
    // Сохранение ответа на сервере
    async function saveAnswerToServer(taskId, answer, isCorrect) {
        try {
            await fetch('/save_answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_id: taskId,
                    answer: answer,
                    is_correct: isCorrect
                })
            });
        } catch (error) {
            console.error('Ошибка сохранения:', error);
        }
    }
    
    // Остальной код остаётся без изменений
    document.querySelectorAll('.btn-check').forEach(button => {
        button.addEventListener('click', function() {
            checkAnswer(this.closest('.task-card'));
        });
    });
    
    // Обновление прогресса
    function updateProgress() {
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        const totalTasks = document.querySelectorAll('.task-card').length;
        const percentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
        
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${completedTasks} из ${totalTasks} заданий`;
    }
});