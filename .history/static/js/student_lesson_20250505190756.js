document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, есть ли сохраненные ответы
    const lessonId = window.location.pathname.split('/').pop();
    const userId = document.querySelector('.task-card')?.dataset.userId;
    
    if (userId) {
        fetch(`/get_student_answers/${lessonId}/${userId}`)
            .then(response => response.json())
            .then(answers => {
                answers.forEach(answer => {
                    const taskCard = document.querySelector(`.task-card[data-task-id="${answer.task_id}"]`);
                    if (taskCard) {
                        const input = taskCard.querySelector('.answer-input');
                        const checkBtn = taskCard.querySelector('.btn-check');
                        const feedback = taskCard.querySelector('.task-feedback');
                        
                        if (answer.answer) {
                            input.value = answer.answer;
                            input.disabled = true;
                            checkBtn.disabled = true;
                            
                            if (answer.is_correct) {
                                taskCard.querySelector('.feedback-correct').classList.remove('hidden');
                            } else {
                                taskCard.querySelector('.feedback-incorrect').classList.remove('hidden');
                            }
                            
                            feedback.classList.remove('hidden');
                        }
                    }
                });
            });
    }
    
    // Проверка ответов
    taskCards.forEach(card => {
        const checkBtn = card.querySelector('.btn-check');
        const answerInput = card.querySelector('.answer-input');
        const feedback = card.querySelector('.task-feedback');
        const correctFeedback = card.querySelector('.feedback-correct');
        const incorrectFeedback = card.querySelector('.feedback-incorrect');
        const hintBtn = card.querySelector('.btn-hint');
        const hint = card.querySelector('.task-hint');
        const status = card.querySelector('.task-status');
        
        checkBtn.addEventListener('click', async function() {
            const userAnswer = answerInput.value.trim();
            const taskId = card.dataset.taskId;
            
            if (!userAnswer) {
                alert('Пожалуйста, введите ответ');
                return;
            }
            
            // Отправка ответа на сервер
            try {
                const response = await fetch('/check_answer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        task_id: taskId,
                        user_answer: userAnswer
                    })
                });
                
                const result = await response.json();
                
                if (result.correct) {
                    // Правильный ответ
                    correctFeedback.classList.remove('hidden');
                    incorrectFeedback.classList.add('hidden');
                    status.style.backgroundColor = 'var(--success-color)';
                    status.style.borderColor = 'var(--success-color)';
                    completedTasks++;
                    updateProgress();
                } else {
                    // Неправильный ответ
                    correctFeedback.classList.add('hidden');
                    incorrectFeedback.classList.remove('hidden');
                    status.style.backgroundColor = 'var(--error-color)';
                    status.style.borderColor = 'var(--error-color)';
                }
                
                feedback.classList.remove('hidden');
                answerInput.disabled = true;
                checkBtn.disabled = true;
                
            } catch (error) {
                console.error('Error:', error);
                alert('Произошла ошибка при проверке ответа');
            }
        });
        
        // Показать подсказку
        hintBtn?.addEventListener('click', function() {
            hint.classList.toggle('hidden');
        });
    });
    
    // Обновление прогресса
    function updateProgress() {
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        const totalTasks = taskCards.length;
        const percentage = (completedTasks / totalTasks) * 100;
        
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${completedTasks} из ${totalTasks} заданий`;
    }
});