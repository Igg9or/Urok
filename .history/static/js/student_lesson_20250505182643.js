document.addEventListener('DOMContentLoaded', function() {
    // Проверка ответов
    document.querySelectorAll('.btn-check').forEach(button => {
        button.addEventListener('click', function() {
            const taskCard = this.closest('.task-card');
            const userAnswer = taskCard.querySelector('.answer-input').value.trim();
            const correctAnswer = taskCard.querySelector('.correct-answer').value;
            const resultDiv = taskCard.querySelector('.result');
            
            if (!userAnswer) {
                alert('Введите ответ');
                return;
            }
            
            // Простая проверка (можно усложнить)
            if (userAnswer == correctAnswer) {
                resultDiv.textContent = 'Правильно!';
                resultDiv.style.color = 'green';
            } else {
                resultDiv.textContent = `Неверно. Правильный ответ: ${correctAnswer}`;
                resultDiv.style.color = 'red';
            }
            
            resultDiv.classList.remove('hidden');
            
            // Можно добавить сохранение результата
            saveAnswer(
                taskCard.dataset.taskId,
                taskCard.dataset.userId,
                userAnswer,
                userAnswer == correctAnswer
            );
        });
    });
    
    function saveAnswer(taskId, userId, answer, isCorrect) {
        fetch('/save_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task_id: taskId,
                user_id: userId,
                answer: answer,
                is_correct: isCorrect
            })
        });
    }
});