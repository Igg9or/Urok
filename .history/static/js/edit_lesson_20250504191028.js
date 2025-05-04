document.addEventListener('DOMContentLoaded', function() {
    const tasksContainer = document.getElementById('tasksContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const saveLessonBtn = document.getElementById('saveLessonBtn');
    const lessonId = window.location.pathname.split('/').pop();

    
    // Добавление нового задания
    addTaskBtn.addEventListener('click', function() {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.innerHTML = `
            <textarea class="task-question" placeholder="Введите вопрос"></textarea>
            <textarea class="task-answer" placeholder="Введите ответ"></textarea>
            <button class="btn btn-danger btn-remove-task">Удалить</button>
        `;
        tasksContainer.appendChild(taskCard);
    });

    // Удаление задания
    tasksContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-remove-task')) {
            const taskCard = e.target.closest('.task-card');
            const taskId = taskCard.dataset.taskId;
            
            if (taskId) {
                // Если задание уже есть в БД - удаляем
                fetch(`/teacher/delete_task/${taskId}`, {
                    method: 'DELETE'
                }).then(response => {
                    if (!response.ok) throw new Error('Ошибка удаления');
                    taskCard.remove();
                });
            } else {
                // Если задание новое - просто удаляем из DOM
                taskCard.remove();
            }
        }
    });

    // Сохранение изменений
    saveLessonBtn.addEventListener('click', function() {
        const tasks = [];
        document.querySelectorAll('.task-card').forEach(taskCard => {
            tasks.push({
                id: taskCard.dataset.taskId || null,
                question: taskCard.querySelector('.task-question').value,
                answer: taskCard.querySelector('.task-answer').value
            });
        });

        fetch(`/teacher/update_lesson/${lessonId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tasks: tasks })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Изменения сохранены!');
                // Обновляем ID новых заданий
                data.tasks.forEach((task, index) => {
                    if (!tasks[index].id) {
                        document.querySelectorAll('.task-card')[index].dataset.taskId = task.id;
                    }
                });
            } else {
                alert('Ошибка сохранения: ' + (data.error || ''));
            }
        });
    });
});