document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    const userId = document.querySelector('.task-card')?.dataset.userId;
    let completedTasks = 0;
    
    // Загрузка сохраненных ответов
    if (userId) {
        fetch(`/get_student_answers/${lessonId}/${userId}`)
            .then(response => {
                if (!response.ok) throw new Error('Network error');
                return response.json();
            })
            .then(answers => {
                answers.forEach(answer => {
                    const taskCard = document.querySelector(`.task-card[data-task-id="${answer.task_id}"]`);
                    if (taskCard) {
                        const input = taskCard.querySelector('.answer-input');
                        const checkBtn = taskCard.querySelector('.btn-check');
                        const feedback = taskCard.querySelector('.task-feedback');
                        const status = taskCard.querySelector('.task-status');
                        
                        if (answer.answer) {
                            input.value = answer.answer;
                            input.disabled = true;
                            checkBtn.disabled = true;
                            
                            if (answer.is_correct) {
                                taskCard.querySelector('.feedback-correct').classList.remove('hidden');
                                status.style.backgroundColor = 'var(--success-color)';
                                status.style.borderColor = 'var(--success-color)';
                                completedTasks++;
                            } else {
                                taskCard.querySelector('.feedback-incorrect').classList.remove('hidden');
                                status.style.backgroundColor = 'var(--error-color)';
                                status.style.borderColor = 'var(--error-color)';
                            }
                            
                            feedback.classList.remove('hidden');
                        }
                    }
                });
                updateProgress();
            })
            .catch(error => {
                console.error('Error loading answers:', error);
            });
    }
    
    // Обработка проверки ответов
    document.querySelectorAll('.btn-check').forEach(button => {
        button.addEventListener('click', async function() {
            const taskCard = this.closest('.task-card');
            const taskId = taskCard.dataset.taskId;
            const userAnswer = taskCard.querySelector('.answer-input').value.trim();
            const correctAnswer = taskCard.querySelector('.correct-answer').textContent;
            const feedback = taskCard.querySelector('.task-feedback');
            const correctFeedback = taskCard.querySelector('.feedback-correct');
            const incorrectFeedback = taskCard.querySelector('.feedback-incorrect');
            const status = taskCard.querySelector('.task-status');
            
            if (!userAnswer) {
                alert('Пожалуйста, введите ответ');
                return;
            }
            
            try {
                const response = await fetch('/check_answer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        lesson_id: lessonId,
                        task_id: taskId,
                        user_id: userId,
                        user_answer: userAnswer,
                        correct_answer: correctAnswer
                    })
                });
                
                if (!response.ok) throw new Error('Server error');
                
                const result = await response.json();
                
                if (result.correct) {
                    // Правильный ответ
                    correctFeedback.classList.remove('hidden');
                    incorrectFeedback.classList.add('hidden');
                    status.style.backgroundColor = 'var(--success-color)';
                    status.style.borderColor = 'var(--success-color)';
                    completedTasks++;
                } else {
                    // Неправильный ответ
                    correctFeedback.classList.add('hidden');
                    incorrectFeedback.classList.remove('hidden');
                    status.style.backgroundColor = 'var(--error-color)';
                    status.style.borderColor = 'var(--error-color)';
                }
                
                feedback.classList.remove('hidden');
                taskCard.querySelector('.answer-input').disabled = true;
                this.disabled = true;
                
                updateProgress();
                
            } catch (error) {
                console.error('Error:', error);
                alert('Произошла ошибка при проверке ответа');
            }
        });
    });
    
    // Показать/скрыть подсказку
    document.querySelectorAll('.btn-hint').forEach(button => {
        button.addEventListener('click', function() {
            const hint = this.closest('.task-feedback').querySelector('.task-hint');
            hint.classList.toggle('hidden');
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
