document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    const tasksContainer = document.getElementById('tasksContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const saveLessonBtn = document.getElementById('saveLessonBtn');
    const textbookSelect = document.getElementById('textbookSelect');
    const templateSearch = document.getElementById('templateSearch');
    const templatesList = document.getElementById('templatesList');

    // Кэш для хранения загруженных шаблонов
    const templatesCache = {};

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
        // Проверяем кэш
        if (templatesCache[templateId]) {
            processTemplate(templatesCache[templateId]);
            return;
        }
        
        fetch(`/api/templates/${templateId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    templatesCache[templateId] = data.template;
                    processTemplate(data.template);
                }
            });
    }

    function processTemplate(template) {
        addTask(template.question_template, template.answer_template);
        
        const taskCard = tasksContainer.lastElementChild;
        taskCard.dataset.templateId = template.id;
        
        // Добавляем отображение параметров
        const paramsDiv = document.createElement('div');
        paramsDiv.className = 'task-params';
        paramsDiv.innerHTML = `
            <h4>Параметры задания:</h4>
            <div class="params-grid">
                ${Object.entries(JSON.parse(template.parameters)).map(([param, config]) => `
                <div class="param-group">
                    <div class="param-name">${param}:</div>
                    <div class="param-range">от ${config.min} до ${config.max}</div>
                    ${config.constraints ? `
                    <div class="param-constraints">
                        ${config.constraints.map(c => `
                        <div class="constraint">
                            <span class="constraint-type">${formatConstraintType(c.type)}:</span>
                            <span class="constraint-value">${c.value}</span>
                        </div>
                        `).join('')}
                    </div>
                    ` : ''}
                </div>
                `).join('')}
            </div>
        `;
        
        taskCard.insertBefore(paramsDiv, taskCard.querySelector('.teacher-preview'));
    }

    function formatConstraintType(type) {
        const types = {
            'multiple_of': 'Кратно',
            'greater_than': 'Больше чем',
            'less_than': 'Меньше чем',
            'equals': 'Равно'
        };
        return types[type] || type;
    }

    // Генерация примера для учителя
    function generateExample(questionTemplate, answerTemplate, taskCard) {
    // Если есть шаблон (template_id), используем его параметры + conditions
    if (taskCard.dataset.templateId && templatesCache[taskCard.dataset.templateId]) {
        const template = templatesCache[taskCard.dataset.templateId];
        
        try {
            // Получаем полные параметры из шаблона (включая conditions)
            const templateParams = JSON.parse(template.parameters);
            
            // Генерируем параметры через MathEngine (учитывает conditions!)
            const params = MathEngine.generate_parameters(templateParams);

            // Проверяем, что параметры сгенерированы с учетом условий
            if (!params || Object.keys(params).length === 0) {
                throw new Error("Не удалось сгенерировать параметры, удовлетворяющие условиям");
            }

            // Заменяем параметры в вопросе
            let exampleQuestion = questionTemplate;
            for (const [param, value] of Object.entries(params)) {
                exampleQuestion = exampleQuestion.replace(
                    new RegExp(`\\{${param}\\}`, 'g'), 
                    value.toString()
                );
            }

            // Вычисляем ответ через MathEngine (для точного вычисления)
            const computedAnswer = MathEngine.evaluate_expression(
                answerTemplate, 
                params
            );

            // Для деления: проверяем, должен ли ответ быть целым
            if (templateParams.conditions && templateParams.conditions.includes('%')) {
                const isDivisionExact = eval(templateParams.conditions.replace(/&&/g, '&&').replace(/\|\|/g, '||'));
                if (isDivisionExact && computedAnswer.includes('.')) {
                    throw new Error("Условие целочисленного деления не выполнено");
                }
            }

            return {
                question: exampleQuestion,
                answer: computedAnswer,
                params: params
            };

        } catch (e) {
            console.error("Ошибка генерации примера:", e);
            return {
                question: "Невозможно сгенерировать пример (нарушены условия шаблона)",
                answer: "—",
                params: {}
            };
        }
    } 
    // Если шаблона нет, генерируем случайные параметры (старый способ)
    else {
        const params = {};
        const allParams = new Set();
        
        // Находим все параметры в вопросе и ответе
        const questionParams = [...questionTemplate.matchAll(/\{([A-Za-z]+)\}/g)];
        const answerParams = [...answerTemplate.matchAll(/\{([A-Za-z]+)\}/g)];
        
        [...questionParams, ...answerParams].forEach(match => {
            allParams.add(match[1]);
        });

        // Генерируем случайные значения
        allParams.forEach(param => {
            params[param] = randomInt(1, 10);
        });

        // Формируем вопрос с подставленными параметрами
        let exampleQuestion = questionTemplate;
        for (const [param, value] of Object.entries(params)) {
            exampleQuestion = exampleQuestion.replace(
                new RegExp(`\\{${param}\\}`, 'g'), 
                value.toString()
            );
        }

        // Вычисляем ответ (простое eval, без сложной логики)
        let exampleAnswer;
        try {
            let answerFormula = answerTemplate;
            for (const [param, value] of Object.entries(params)) {
                answerFormula = answerFormula.replace(
                    new RegExp(`\\{${param}\\}`, 'g'), 
                    value.toString()
                );
            }
            exampleAnswer = safeEval(answerFormula)?.toString() ?? "Ошибка в формуле";
        } catch (e) {
            exampleAnswer = "Ошибка вычисления";
        }

        return {
            question: exampleQuestion,
            answer: exampleAnswer,
            params: params
        };
    }
}

    function randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
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
        
        const example = generateExample(question, answer, taskCard);
        
        taskCard.querySelector('.preview-question').textContent = example.question;
        taskCard.querySelector('.preview-answer').textContent = example.answer;
        taskCard.querySelector('.preview-params').textContent = 
            Object.entries(example.params).map(([k, v]) => `${k}=${v}`).join(', ');
        
        preview.classList.remove('hidden');
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
                answer: taskCard.querySelector('.task-answer').value,
                template_id: taskCard.dataset.templateId || null  // Добавляем template_id
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