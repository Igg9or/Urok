document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    const tasksContainer = document.getElementById('tasksContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const saveLessonBtn = document.getElementById('saveLessonBtn');
    const textbookSelect = document.getElementById('textbookSelect');
    const templateSearch = document.getElementById('templateSearch');
    const templatesList = document.getElementById('templatesList');

    // Загрузка шаблонов из учебника
    textbookSelect.addEventListener('change', loadTemplates);
    templateSearch.addEventListener('input', filterTemplates);

    // Добавление задания из шаблона
    templatesList.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-use-template')) {
            const templateId = e.target.dataset.templateId;
            addTaskFromTemplate(templateId);
        }
    });

    // Загрузка шаблонов
    function loadTemplates() {
        const textbookId = textbookSelect.value;
        if (!textbookId) {
            templatesList.innerHTML = '<div class="empty-state"><p>Выберите учебник для просмотра заданий</p></div>';
            return;
        }

        fetch(`/api/textbooks/${textbookId}/templates`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderTemplates(data.templates);
                }
            });
    }

    // Фильтрация шаблонов
    function filterTemplates() {
        const searchTerm = templateSearch.value.toLowerCase();
        const items = templatesList.querySelectorAll('.template-item');
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    }

    // Отображение шаблонов
    function renderTemplates(templates) {
        if (templates.length === 0) {
            templatesList.innerHTML = '<div class="empty-state"><p>В этом учебнике нет шаблонов заданий</p></div>';
            return;
        }

        templatesList.innerHTML = templates.map(template => `
            <div class="template-item">
                <h4>${template.name}</h4>
                <p>${template.question_template}</p>
                <div class="template-actions">
                    <button class="btn btn-small btn-use-template" data-template-id="${template.id}">
                        Добавить в урок
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Добавление задания из шаблона
    function addTaskFromTemplate(templateId) {
        fetch(`/api/templates/${templateId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const template = data.template;
                    addTask(template.question_template, template.answer_template);
                }
            });
    }

    // Добавление нового задания
    function addTask(question = '', answer = '') {
        const taskNumber = tasksContainer.children.length + 1;
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.innerHTML = `
            <div class="task-header">
                <h3>Задание <span class="task-number">${taskNumber}</span></h3>
                <button class="btn btn-danger btn-remove-task">Удалить</button>
            </div>
            <textarea class="task-question">${question}</textarea>
            <div class="answer-section">
                <label>Формула ответа:</label>
                <textarea class="task-answer">${answer}</textarea>
            </div>
        `;
        tasksContainer.appendChild(taskCard);
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

    // Обновление нумерации заданий
    function updateTaskNumbers() {
        document.querySelectorAll('.task-card').forEach((card, index) => {
            card.querySelector('.task-number').textContent = index + 1;
        });
    }

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
    

    // Добавление пустого задания
    addTaskBtn.addEventListener('click', function() {
        addTask();
    });
});