document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    const tasksContainer = document.getElementById('tasksContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const saveLessonBtn = document.getElementById('saveLessonBtn');
    const templateSource = document.getElementById('templateSource');
    const textbookSelection = document.getElementById('textbookSelection');
    const lessonTemplatesSelection = document.getElementById('lessonTemplatesSelection');

    // Переключение между источниками заданий
    templateSource.addEventListener('change', function() {
        textbookSelection.classList.add('hidden');
        lessonTemplatesSelection.classList.add('hidden');
        
        if (this.value === 'textbook') {
            textbookSelection.classList.remove('hidden');
        } else if (this.value === 'lesson_template') {
            lessonTemplatesSelection.classList.remove('hidden');
        }
    });

    // Загрузка шаблонов из учебника
    document.getElementById('loadTextbookTemplates').addEventListener('click', function() {
        const textbookId = document.getElementById('textbookSelect').value;
        fetch(`/api/textbooks/${textbookId}/templates`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showTemplateSelection(data.templates, 'textbook');
                }
            });
    });

    // Добавление задания из шаблона урока
    document.getElementById('lessonTemplateSelect').addEventListener('change', function() {
        const templateId = this.value;
        if (!templateId) return;
        
        fetch(`/api/lesson_templates/${templateId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addTaskFromTemplate(data.template);
                }
            });
    });

    // Показать выбор шаблонов
    function showTemplateSelection(templates, source) {
        // Здесь можно реализовать модальное окно с выбором шаблона
        // Для простоты добавим первый шаблон
        if (templates.length > 0) {
            addTaskFromTemplate(templates[0], source);
        }
    }

    // Добавить задание из шаблона
    function addTaskFromTemplate(template, source = 'lesson_template') {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.innerHTML = `
            <div class="task-header">
                <h3>Задание <span class="task-number">${tasksContainer.children.length + 1}</span></h3>
                <button class="btn btn-danger btn-remove-task">Удалить</button>
            </div>
            <textarea class="task-question">${template.question_template}</textarea>
            <div class="answer-section">
                <label>Формула ответа:</label>
                <textarea class="task-answer">${template.answer_template}</textarea>
            </div>
        `;
        tasksContainer.appendChild(taskCard);
        updateTaskNumbers();
    }

    // Добавление пустого задания
    function addEmptyTask() {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.innerHTML = `
            <div class="task-header">
                <h3>Задание <span class="task-number">${tasksContainer.children.length + 1}</span></h3>
                <button class="btn btn-danger btn-remove-task">Удалить</button>
            </div>
            <textarea class="task-question" placeholder="Введите вопрос с параметрами {A}, {B}..."></textarea>
            <div class="answer-section">
                <label>Формула ответа:</label>
                <textarea class="task-answer" placeholder="Введите формулу с параметрами {A}, {B}..."></textarea>
            </div>
        `;
        tasksContainer.appendChild(taskCard);
        updateTaskNumbers();
    }

    // Обновление нумерации заданий
    function updateTaskNumbers() {
        const taskCards = document.querySelectorAll('.task-card');
        taskCards.forEach((card, index) => {
            card.querySelector('.task-number').textContent = index + 1;
        });
    }

    // Удаление задания
    tasksContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-remove-task')) {
            const taskCard = e.target.closest('.task-card');
            const taskId = taskCard.dataset.taskId;
            
            if (taskId) {
                fetch(`/teacher/delete_task/${taskId}`, {
                    method: 'DELETE'
                }).then(response => {
                    if (response.ok) {
                        taskCard.remove();
                        updateTaskNumbers();
                    }
                });
            } else {
                taskCard.remove();
                updateTaskNumbers();
            }
        }
    });

    // Сохранение урока
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
            }
        });
    });

    // Инициализация
    addTaskBtn.addEventListener('click', function() {
        const source = templateSource.value;
        
        if (source === 'manual') {
            addEmptyTask();
        } else if (source === 'lesson_template') {
            const templateId = document.getElementById('lessonTemplateSelect').value;
            if (templateId) {
                fetch(`/api/lesson_templates/${templateId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            addTaskFromTemplate(data.template);
                        }
                    });
            }
        }
    });
});