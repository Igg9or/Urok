document.addEventListener('DOMContentLoaded', function() {
    const tasksContainer = document.getElementById('tasksContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const saveLessonBtn = document.getElementById('saveLessonBtn');
    const lessonId = window.location.pathname.split('/').pop();

    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    // Функция для генерации примера
    function generateExample(question, answer) {
        // Находим все параметры в вопросе
        const paramRegex = /\{([A-Z])\}/g;
        const params = {};
        let match;
        
        // Заполняем параметры случайными значениями
        while ((match = paramRegex.exec(question)) !== null) {
            if (!params[match[1]]) {
                params[match[1]] = getRandomInt(1, 10);
            }
        }
        
        // Заменяем параметры в вопросе
        let exampleQuestion = question;
        for (const param in params) {
            exampleQuestion = exampleQuestion.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
        }
        
        // Заменяем параметры в ответе и вычисляем результат
        let exampleAnswer = answer;
        for (const param in params) {
            exampleAnswer = exampleAnswer.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
        }
        
        try {
            exampleAnswer = eval(exampleAnswer).toString();
        } catch (e) {
            exampleAnswer = "Неверная формула ответа";
        }
        
        return {
            question: exampleQuestion,
            answer: exampleAnswer,
            params: params
        };
    }

    // Функция для обновления превью
    function updatePreview(taskCard) {
        const question = taskCard.querySelector('.task-question').value;
        const answer = taskCard.querySelector('.task-answer').value;
        const previewContainer = taskCard.querySelector('.preview-examples');
        
        if (!question || !answer) {
            previewContainer.innerHTML = '<p>Введите вопрос и формулу ответа</p>';
            return;
        }
        
        const example = generateExample(question, answer);
        previewContainer.innerHTML = `
            <div class="example">
                <p><strong>Вопрос:</strong> ${example.question}</p>
                <p><strong>Ответ:</strong> ${example.answer}</p>
                <p class="params">Параметры: ${JSON.stringify(example.params)}</p>
            </div>
        `;
    }

    
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