// static/js/edit_lesson.js
document.addEventListener('DOMContentLoaded', function() {
    const tasksContainer = document.getElementById('tasksContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const saveLessonBtn = document.getElementById('saveLessonBtn');
    const lessonId = window.location.pathname.split('/').pop();

    // ===== ОБЩИЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАДАНИЯМИ =====
    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    async function generateTaskVariant(taskCard) {
        const question = taskCard.querySelector('.task-question').value;
        const answer = taskCard.querySelector('.task-answer').value;
        const paramsJson = taskCard.querySelector('.template-params')?.dataset.params;
        const previewContainer = taskCard.querySelector('.preview-examples');
        
        if (!question || !answer) {
            previewContainer.innerHTML = '<p>Введите вопрос и формулу ответа</p>';
            return;
        }
        
        try {
            const parameters = paramsJson ? JSON.parse(paramsJson) : {};
            const paramMatches = [...new Set(question.match(/\{([A-Za-z]+)\}/g) || [])];
            
            // Если параметров нет в шаблоне, создаем базовые
            if (paramMatches.length > 0 && Object.keys(parameters).length === 0) {
                paramMatches.forEach(param => {
                    const cleanParam = param.replace(/\{|\}/g, '');
                    parameters[cleanParam] = { min: 1, max: 10 };
                });
            }

            const response = await fetch('/api/generate_task_examples', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    question: question,
                    answer: answer,
                    parameters: parameters
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                let html = '';
                data.examples.forEach(example => {
                    html += `
                        <div class="example">
                            <p><strong>Вопрос:</strong> ${example.question}</p>
                            <p><strong>Ответ:</strong> ${example.correct_answer}</p>
                            ${example.params ? `<p class="params">Параметры: ${JSON.stringify(example.params)}</p>` : ''}
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

    textbookSelect.addEventListener('change', loadTemplates);
    templateSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const items = templateItems.querySelectorAll('.template-item');
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? 'block' : 'none';
        });
    });

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

    async function addTemplateToLesson(templateId) {
        try {
            const response = await fetch(`/api/templates/${templateId}`);
            const data = await response.json();
            
            if (data.success) {
                createTaskFromTemplate(data.template);
            } else {
                throw new Error(data.error || 'Ошибка загрузки шаблона');
            }
        } catch (error) {
            console.error('Ошибка добавления шаблона:', error);
            alert('Не удалось добавить шаблон');
        }
    }

    // ===== СОЗДАНИЕ И УПРАВЛЕНИЕ ЗАДАНИЯМИ =====
    function createTaskFromTemplate(template) {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        
        // Парсим параметры шаблона
        const params = JSON.parse(template.parameters);
        const paramsHint = Object.keys(params).map(p => {
            return `${p} (${params[p].min}-${params[p].max})`;
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
                <div class="template-params" data-params='${JSON.stringify(params)}'></div>
            </div>
        `;
        
        tasksContainer.appendChild(taskCard);
        updateTaskNumbers();
        generateTaskVariant(taskCard);
        
        taskCard.querySelector('.task-question').addEventListener('input', () => generateTaskVariant(taskCard));
        taskCard.querySelector('.task-answer').addEventListener('input', () => generateTaskVariant(taskCard));
        taskCard.scrollIntoView({ behavior: 'smooth' });
    }

    function createEmptyTask() {
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
                <div class="template-params hidden" data-params='{}'></div>
            </div>
        `;
        
        tasksContainer.appendChild(taskCard);
        updateTaskNumbers();
        
        taskCard.querySelector('.task-question').addEventListener('input', () => generateTaskVariant(taskCard));
        taskCard.querySelector('.task-answer').addEventListener('input', () => generateTaskVariant(taskCard));
    }

    // ===== ОСНОВНЫЕ ОБРАБОТЧИКИ =====
    addTaskBtn.addEventListener('click', createEmptyTask);

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

    saveLessonBtn.addEventListener('click', function() {
        const tasks = [];
        document.querySelectorAll('.task-card').forEach(taskCard => {
            tasks.push({
                id: taskCard.dataset.taskId || null,
                question: taskCard.querySelector('.task-question').value,
                answer: taskCard.querySelector('.task-answer').value,
                parameters: taskCard.querySelector('.template-params')?.dataset.params || '{}'
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

    // Инициализация
    document.querySelectorAll('.task-card').forEach(taskCard => {
        taskCard.querySelector('.task-question').addEventListener('input', () => generateTaskVariant(taskCard));
        taskCard.querySelector('.task-answer').addEventListener('input', () => generateTaskVariant(taskCard));
        generateTaskVariant(taskCard);
    });

    loadTemplates();
});