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
    function generateExample(questionTemplate, answerTemplate) {
        // Находим параметры в шаблоне
        const paramRegex = /\{([A-Za-z]+)\}/g;
        const params = {};
        let match;
        
        // Генерируем случайные значения для параметров
        while ((match = paramRegex.exec(questionTemplate + answerTemplate)) {
            const param = match[1];
            if (!params[param]) {
                params[param] = Math.floor(Math.random() * 10) + 1; // Значения от 1 до 10
            }
        }
        
        // Заменяем параметры в вопросе
        let exampleQuestion = questionTemplate;
        for (const [param, value] of Object.entries(params)) {
            exampleQuestion = exampleQuestion.replace(new RegExp(`\\{${param}\\}`, 'g'), value);
        }
        
        // Вычисляем ответ
        let exampleAnswer;
        try {
            // Заменяем параметры в формуле ответа
            let answerFormula = answerTemplate;
            for (const [param, value] of Object.entries(params)) {
                answerFormula = answerFormula.replace(new RegExp(`\\{${param}\\}`, 'g'), value);
            }
            // Вычисляем ответ (осторожно с eval!)
            exampleAnswer = eval(answerFormula).toString();
        } catch (e) {
            exampleAnswer = "Ошибка в формуле ответа";
        }
        
        return {
            question: exampleQuestion,
            answer: exampleAnswer,
            params: params
        };
    }

    function updatePreview(taskCard) {
        const question = taskCard.querySelector('.task-question').value;
        const answer = taskCard.querySelector('.task-answer').value;
        const preview = taskCard.querySelector('.teacher-preview');
        
        if (!question || !answer) {
            return;
        }
        
        const example = generateExample(question, answer);
        
        taskCard.querySelector('.preview-question').textContent = example.question;
        taskCard.querySelector('.preview-answer').textContent = example.answer;
        taskCard.querySelector('.preview-params').textContent = 
            Object.entries(example.params).map(([k, v]) => `${k}=${v}`).join(', ');
        
        preview.classList.remove('hidden');
    }

    // Обработчики для кнопок предпросмотра
    document.addEventListener('click', function(e) {
        // Показать/скрыть превью
        if (e.target.classList.contains('btn-show-preview')) {
            const taskCard = e.target.closest('.task-card');
            const preview = taskCard.querySelector('.teacher-preview');
            const isHidden = preview.classList.contains('hidden');
            
            if (isHidden) {
                updatePreview(taskCard);
            } else {
                preview.classList.add('hidden');
            }
            e.target.textContent = isHidden ? 'Скрыть пример' : 'Показать пример';
        }
        
        // Сгенерировать новый пример
        if (e.target.classList.contains('btn-generate-preview')) {
            const taskCard = e.target.closest('.task-card');
            updatePreview(taskCard);
        }
    });

    // Добавление пустого задания
    addTaskBtn.addEventListener('click', function() {
        addTask();
    });
});