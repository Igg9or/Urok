// Исправленная версия edit_lesson.js

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
                    const params = template.parameters;
                    const conditions = template.conditions || '';
                    const paramsInfo = generateParamsInfo(params, conditions);
                    
                    const taskElement = addTask(template.question_template, template.answer_template, paramsInfo);
                    
                    // Сохраняем параметры в data-атрибут
                    if (params) {
                        taskElement.dataset.params = typeof params === 'string' ? params : JSON.stringify(params);
                    }
                }
            });
    }

    function generateParamsInfo(parameters, conditions) {
        let html = '<div class="template-params">';
        html += '<h4>Параметры задания:</h4>';
        
        try {
            // Пытаемся разобрать параметры, если они в формате JSON
            const paramsObj = typeof parameters === 'string' ? JSON.parse(parameters) : parameters;
            
            if (paramsObj && typeof paramsObj === 'object') {
                html += '<ul class="params-list">';
                
                for (const [param, config] of Object.entries(paramsObj)) {
                    if (param === 'conditions') continue;
                    
                    html += `<li><strong>${param}:</strong>`;
                    
                    if (config && typeof config === 'object') {
                        html += ` ${config.min || 1} ≤ ${param} ≤ ${config.max || 10}`;
                        
                        if (config.constraints && config.constraints.length > 0) {
                            html += '<ul class="constraints-list">';
                            for (const constraint of config.constraints) {
                                if (constraint.type === 'multiple_of') {
                                    html += `<li>Кратно ${constraint.value}</li>`;
                                } else if (constraint.type === 'greater_than') {
                                    html += `<li>Больше чем ${constraint.value}</li>`;
                                }
                            }
                            html += '</ul>';
                        }
                    } else {
                        html += ' (неправильный формат параметров)';
                    }
                    
                    html += '</li>';
                }
                
                html += '</ul>';
            } else {
                html += '<p>Параметры не заданы или имеют неправильный формат</p>';
            }
        } catch (e) {
            console.error('Error parsing parameters:', e);
            html += '<p>Ошибка при разборе параметров</p>';
        }
        
        if (conditions) {
            html += '<div class="conditions-info">';
            html += '<h4>Условия задачи:</h4>';
            html += `<p>${formatConditions(conditions)}</p>`;
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }

    function formatConditions(conditions) {
        // Форматируем условия для лучшей читаемости
        return conditions
            .replace(/%/g, ' mod ')
            .replace(/&&/g, 'И')
            .replace(/\|\|/g, 'ИЛИ')
            .replace(/==/g, '=')
            .replace(/!=/g, '≠');
    }

    // Генерация примера для учителя
    function generateExample(questionTemplate, answerTemplate, paramsConfig = null) {
        const params = {};
        let question = questionTemplate;
        let answer = answerTemplate;

        // Если есть конфигурация параметров из шаблона
        if (paramsConfig) {
            try {
                // Парсим параметры, если они в формате JSON
                const config = typeof paramsConfig === 'string' ? JSON.parse(paramsConfig) : paramsConfig;

                for (const [param, paramConfig] of Object.entries(config)) {
                    if (param === 'conditions') continue;

                    // Генерируем значение с учетом ограничений
                    let value;
                    let valid = false;
                    let attempts = 0;
                    const maxAttempts = 100;

                    while (!valid && attempts < maxAttempts) {
                        // Генерируем случайное значение в диапазоне
                        value = getRandomInt(paramConfig.min, paramConfig.max);

                        // Проверяем ограничения
                        valid = checkConstraints(value, paramConfig.constraints || []);

                        attempts++;
                    }

                    // Если не удалось сгенерировать подходящее значение, берем минимальное
                    params[param] = valid ? value : paramConfig.min;
                }
            } catch (e) {
                console.error('Error parsing params config:', e);
                // Если ошибка парсинга, генерируем простые значения
                generateSimpleParams(question + answer, params);
            }
        } else {
            // Если нет конфигурации, генерируем простые значения
            generateSimpleParams(question + answer, params);
        }

        // Заменяем параметры в вопросе и ответе
        for (const [param, value] of Object.entries(params)) {
            question = question.replace(new RegExp(`\\{${param}\\}`, 'g'), value);
            answer = answer.replace(new RegExp(`\\{${param}\\}`, 'g'), value);
        }

        // Вычисляем ответ
        let computedAnswer;
        try {
            computedAnswer = safeEval(answer)?.toString() ?? "Ошибка в формуле";
        } catch (e) {
            console.error('Error evaluating answer:', e);
            computedAnswer = "Ошибка в формуле ответа";
        }

        return {
            question: question,
            answer: computedAnswer,
            params: params
        };
    }

    function generateSimpleParams(template, params) {
        const paramRegex = /\{([A-Za-z]+)\}/g;
        let match;
        
        while ((match = paramRegex.exec(template))) {
            const param = match[1];
            if (!params[param]) {
                params[param] = Math.floor(Math.random() * 10) + 1;
            }
        }
    }

    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    function checkConstraints(value, constraints) {
        if (!constraints || constraints.length === 0) return true;

        for (const constraint of constraints) {
            switch (constraint.type) {
                case 'multiple_of':
                    if (value % constraint.value !== 0) return false;
                    break;
                case 'greater_than':
                    if (value <= constraint.value) return false;
                    break;
                case 'less_than':
                    if (value >= constraint.value) return false;
                    break;
                case 'equals':
                    if (value !== constraint.value) return false;
                    break;
            }
        }
        return true;
    }

    // Безопасное вычисление выражения
    function safeEval(formula) {
        // Удаляем все потенциально опасные символы
        const cleanFormula = formula.replace(/[^0-9+\-*/().{}\s]/g, '');
        try {
            return new Function('return ' + cleanFormula)();
        } catch (e) {
            console.error('Ошибка вычисления:', e);
            return null;
        }
    }

    // Обновление предпросмотра
    function updatePreview(taskCard) {
        const question = taskCard.querySelector('.task-question').value;
        const answer = taskCard.querySelector('.task-answer').value;
        const preview = taskCard.querySelector('.teacher-preview');
        
        if (!question || !answer) {
            preview.classList.add('hidden');
            return;
        }
        
        // Проверяем, есть ли информация о параметрах в шаблоне
        const paramsConfigElement = taskCard.querySelector('.template-params');
        let paramsConfig = null;
        
        if (paramsConfigElement) {
            try {
                // Извлекаем параметры из data-атрибута или другого места, где они сохранены
                // В данном примере предполагаем, что параметры хранятся в data-params
                paramsConfig = taskCard.dataset.params ? JSON.parse(taskCard.dataset.params) : null;
            } catch (e) {
                console.error('Error parsing params config', e);
            }
        }
        
        const example = generateExample(question, answer, paramsConfig);
        
        taskCard.querySelector('.preview-question').textContent = example.question;
        taskCard.querySelector('.preview-answer').textContent = example.answer;
        taskCard.querySelector('.preview-params').textContent = 
            Object.entries(example.params).map(([k, v]) => `${k}=${v}`).join(', ');
        
        preview.classList.remove('hidden');
    }

    // Добавление нового задания
    function addTask(question = '', answer = '', paramsInfo = '') {
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
            ${paramsInfo || ''}
            <div class="teacher-preview hidden">
                <h4>Пример для учителя:</h4>
                <div class="preview-content">
                    <p><strong>Пример задания:</strong> <span class="preview-question"></span></p>
                    <p><strong>Правильный ответ:</strong> <span class="preview-answer"></span></p>
                    <p><strong>Используемые параметры:</strong> <span class="preview-params"></span></p>
                </div>
                <button class="btn btn-small btn-generate-preview">Сгенерировать новый пример</button>
            </div>
            <button class="btn btn-small btn-show-preview">Показать пример</button>
        `;
        tasksContainer.appendChild(taskCard);
        
        // Если добавляем из шаблона, сразу показываем пример
        if (question && answer) {
            const previewBtn = taskCard.querySelector('.btn-show-preview');
            previewBtn.click();
        }
    }

    // Обновление нумерации заданий
    function updateTaskNumbers() {
        document.querySelectorAll('.task-card').forEach((card, index) => {
            card.querySelector('.task-number').textContent = index + 1;
        });
    }

    // Обработчики событий
    document.addEventListener('click', function(e) {
        // Показать/скрыть превью
        if (e.target.classList.contains('btn-show-preview')) {
            const taskCard = e.target.closest('.task-card');
            const preview = taskCard.querySelector('.teacher-preview');
            const isHidden = preview.classList.contains('hidden');
            
            if (isHidden) {
                updatePreview(taskCard);
                e.target.textContent = 'Скрыть пример';
            } else {
                preview.classList.add('hidden');
                e.target.textContent = 'Показать пример';
            }
        }
        
        // Сгенерировать новый пример
        if (e.target.classList.contains('btn-generate-preview')) {
            const taskCard = e.target.closest('.task-card');
            updatePreview(taskCard);
        }
    });

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

    // Добавление пустого задания
    addTaskBtn.addEventListener('click', function() {
        addTask();
    });
});