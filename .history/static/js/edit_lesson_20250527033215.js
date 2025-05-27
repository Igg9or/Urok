document.addEventListener('DOMContentLoaded', function() {
    const tasksContainer = document.getElementById('tasksContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const saveLessonBtn = document.getElementById('saveLessonBtn');
    const lessonId = window.location.pathname.split('/').pop();

    // ===== ОСНОВНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАДАНИЯМИ =====
    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    function generateExample(question, answer) {
        const paramsEl = document.querySelector('.template-params');
        const params = paramsEl ? JSON.parse(paramsEl.dataset.params) : {};
        
        // Генерация значений с учетом ограничений
        const values = {};
        for (const param in params) {
            let valid = false;
            let value;
            const config = params[param];
            
            // Пытаемся сгенерировать значение, удовлетворяющее всем условиям
            for (let i = 0; i < 100 && !valid; i++) {
                value = config.type === 'float' ? 
                    getRandomFloat(config.min, config.max) :
                    getRandomInt(config.min, config.max);
                
                valid = true;
                
                // Проверяем ограничения
                if (config.constraints) {
                    for (const constraint of config.constraints) {
                        if (constraint.type === 'multiple_of' && value % constraint.value !== 0) {
                            valid = false;
                        } else if (constraint.type === 'greater_than') {
                            const compareTo = constraint.param ? values[constraint.param] : constraint.value;
                            if (value <= compareTo) valid = false;
                        }
                        // другие проверки
                    }
                }
            }
            
            values[param] = value || config.min; // fallback
        }
        
        // Заменяем параметры в вопросе и ответе
        let exampleQuestion = question;
        let exampleAnswer = answer;
        
        for (const param in values) {
            const value = values[param];
            exampleQuestion = exampleQuestion.replace(new RegExp(`\\{${param}\\}`, 'g'), value);
            exampleAnswer = exampleAnswer.replace(new RegExp(`\\{${param}\\}`, 'g'), value);
        }
        
        try {
            exampleAnswer = eval(exampleAnswer).toString();
        } catch (e) {
            exampleAnswer = "Неверная формула ответа";
        }
        
        return {
            question: exampleQuestion,
            answer: exampleAnswer,
            params: values
        };
    }

    async function updatePreview(taskCard) {
    const question = taskCard.querySelector('.task-question').value;
    const answer = taskCard.querySelector('.task-answer').value;
    const previewContainer = taskCard.querySelector('.preview-examples');
    
    if (!question || !answer) {
        previewContainer.innerHTML = '<p>Введите вопрос и формулу ответа</p>';
        return;
    }
    
    try {
        const response = await fetch('/api/generate_task_examples', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                question: question,
                answer: answer,
                parameters: getParametersFromTaskCard(taskCard)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let html = '';
            data.examples.forEach(example => {
                html += `
                    <div class="example">
                        <p><strong>Вопрос:</strong> ${example.question}</p>
                        <p><strong>Ответ:</strong> ${example.answer}</p>
                        <p class="params">Параметры: ${JSON.stringify(example.params)}</p>
                    </div>
                `;
            });
            previewContainer.innerHTML = html;
        } else {
            previewContainer.innerHTML = `<p>Ошибка: ${data.error || 'Неизвестная ошибка'}</p>`;
        }
    } catch (error) {
        previewContainer.innerHTML = '<p>Ошибка соединения с сервером</p>';
    }
}


    function updateTaskNumbers() {
        const taskCards = document.querySelectorAll('.task-card');
        taskCards.forEach((card, index) => {
            card.querySelector('.task-number').textContent = index + 1;
        });
    }

    // ===== ФУНКЦИОНАЛ ШАБЛОНОВ ИЗ УЧЕБНИКОВ =====
    const textbookSelect = document.getElementById('textbookSelect');
    const templateItems = document.getElementById('templateItems');
    const templateSearch = document.getElementById('templateSearch');

    // Загрузка шаблонов при изменении учебника
    textbookSelect.addEventListener('change', loadTemplates);

    // Поиск шаблонов
    templateSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const items = templateItems.querySelectorAll('.template-item');
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    });

    // Загрузка шаблонов из учебника
    async function loadTemplates() {
        
        const textbookId = textbookSelect.value;
        
        
        try {
            const response = await fetch(`/api/textbooks/${textbookId}/templates`);
            const data = await response.json();
            
            if (data.success) {
                renderTemplates(data.templates);
            } else {
                throw new Error(data.error || 'Ошибка загрузки шаблонов');
            }
        } catch (error) {
            console.error('Ошибка загрузки шаблонов:', error);
            alert('Не удалось загрузить шаблоны');
        }
    }

    // Отображение списка шаблонов
    function renderTemplates(templates) {
        templateItems.innerHTML = templates.length ? '' : '<p>Нет шаблонов для этого учебника</p>';
        
        templates.forEach(template => {
            const item = document.createElement('div');
            item.className = 'template-item';
            item.innerHTML = `
                <h4>${template.name}</h4>
                <p>${template.question_template}</p>
                <div class="template-actions">
                    <button class="btn btn-small btn-add-template" data-id="${template.id}">Добавить</button>
                    <button class="btn btn-small btn-preview-template">Пример</button>
                </div>
            `;
            templateItems.appendChild(item);
        });

        // Обработчики для кнопок шаблонов
        templateItems.querySelectorAll('.btn-add-template').forEach(btn => {
            btn.addEventListener('click', function() {
                const templateId = this.dataset.id;
                addTemplateToLesson(templateId);
            });
        });

        templateItems.querySelectorAll('.btn-preview-template').forEach(btn => {
            btn.addEventListener('click', function() {
                const templateItem = this.closest('.template-item');
                const question = templateItem.querySelector('p').textContent;
                alert(`Пример задания:\n\n${question}`);
            });
        });
    }

    // Добавление шаблона в урок
    async function addTemplateToLesson(templateId) {
        try {
            const response = await fetch(`/api/templates/${templateId}`);
            const data = await response.json();
            
            if (data.success) {
                const template = data.template;
                createTaskFromTemplate(template);
            } else {
                throw new Error(data.error || 'Ошибка загрузки шаблона');
            }
        } catch (error) {
            console.error('Ошибка добавления шаблона:', error);
            alert('Не удалось добавить шаблон');
        }
    }

    // Создание задания из шаблона
    function createTaskFromTemplate(template) {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        
        // Парсим параметры шаблона
        const params = JSON.parse(template.parameters);
        const paramsHint = Object.keys(params).map(p => {
            const constraints = params[p].constraints?.map(c => {
                if (c.type === 'multiple_of') return `кратно ${c.value}`;
                if (c.type === 'greater_than') return `> ${c.param || c.value}`;
                // другие типы условий
                return `${c.type} ${c.param || c.value}`;
            }).join(', ');
            
            return `${p} (${params[p].min}-${params[p].max}${constraints ? ', ' + constraints : ''})`;
        }).join(', ');

        taskCard.innerHTML = `
            <div class="task-header">
                <h3>Задание <span class="task-number">${tasksContainer.children.length + 1}</span></h3>
                <button class="btn btn-danger btn-remove-task">Удалить</button>
            </div>
            <textarea class="task-question">${template.question_template}</textarea>
            <div class="task-preview">
                <h4>Пример для учителя:</h4>
                <div class="preview-examples"></div>
            </div>
            <div class="answer-section">
                <label>Формула ответа:</label>
                <textarea class="task-answer">${template.answer_template}</textarea>
                <p class="hint">Используйте параметры: ${paramsHint}</p>
                <div class="template-params hidden" data-params='${JSON.stringify(params)}'></div>
            </div>
        `;
        
        tasksContainer.appendChild(taskCard);
        updateTaskNumbers();
        updatePreview(taskCard);
        
        // Добавляем обработчики для нового задания
        taskCard.querySelector('.task-question').addEventListener('input', () => updatePreview(taskCard));
        taskCard.querySelector('.task-answer').addEventListener('input', () => updatePreview(taskCard));
        
        // Прокручиваем к новому заданию
        taskCard.scrollIntoView({ behavior: 'smooth' });
    }

    // ===== ОСНОВНОЙ ФУНКЦИОНАЛ РЕДАКТИРОВАНИЯ УРОКА =====
    // Добавление нового задания
    addTaskBtn.addEventListener('click', function() {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.innerHTML = `
            <div class="task-header">
                <h3>Задание <span class="task-number">1</span></h3>
                <button class="btn btn-danger btn-remove-task">Удалить</button>
            </div>
            <textarea class="task-question" placeholder="Введите вопрос с параметрами {A}, {B}..."></textarea>
            <div class="task-preview">
                <h4>Пример для учителя:</h4>
                <div class="preview-examples"></div>
            </div>
            <div class="answer-section">
                <label>Формула ответа:</label>
                <textarea class="task-answer" placeholder="Введите формулу с параметрами {A}, {B}..."></textarea>
                <p class="hint">Например: для вопроса "{A} + {B}" формула ответа будет "{A} + {B}"</p>
            </div>
        `;
        
        tasksContainer.appendChild(taskCard);
        updateTaskNumbers();
        
        // Добавляем обработчики для обновления превью
        taskCard.querySelector('.task-question').addEventListener('input', () => updatePreview(taskCard));
        taskCard.querySelector('.task-answer').addEventListener('input', () => updatePreview(taskCard));
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
                    if (!response.ok) throw new Error('Ошибка удаления');
                    taskCard.remove();
                    updateTaskNumbers();
                });
            } else {
                taskCard.remove();
                updateTaskNumbers();
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

    // Инициализация превью для существующих заданий
    document.querySelectorAll('.task-card').forEach(taskCard => {
        taskCard.querySelector('.task-question').addEventListener('input', () => updatePreview(taskCard));
        taskCard.querySelector('.task-answer').addEventListener('input', () => updatePreview(taskCard));
        updatePreview(taskCard);
    });

    // Первоначальная загрузка шаблонов
    loadTemplates();
});