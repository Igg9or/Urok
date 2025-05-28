document.addEventListener('DOMContentLoaded', function() {
    // Конфигурация
    const textbookId = document.querySelector('.textbook-tasks-container').dataset.textbookId;
    const API_BASE = '/api';
    const TEXTS = {
        deleteConfirm: 'Удалить этот шаблон задания?',
        saveSuccess: 'Шаблон успешно сохранён',
        deleteSuccess: 'Шаблон удалён'
    };

    // Элементы
    const elements = {
        showFormBtn: document.getElementById('showFormBtn'),
        taskForm: document.getElementById('taskForm'),
        cancelBtn: document.getElementById('cancelBtn'),
        saveBtn: document.getElementById('saveTemplateBtn'),
        templatesList: document.getElementById('templatesList'),
        formTitle: document.querySelector('#taskForm h3'),
        templateName: document.getElementById('templateName'),
        questionTemplate: document.getElementById('questionTemplate'),
        answerTemplate: document.getElementById('answerTemplate'),
        paramsContainer: document.getElementById('paramsContainer')
    };

    // Текущее состояние
    let state = {
        currentTemplateId: null,
        isEditing: false
    };

    // ===== ОСНОВНЫЕ ФУНКЦИИ =====
    function toggleForm(show = true) {
        elements.taskForm.classList.toggle('hidden', !show);
        if (show) {
            elements.formTitle.textContent = state.isEditing 
                ? 'Редактирование шаблона' 
                : 'Новый шаблон задания';
        }
    }

    function resetForm() {
        elements.templateName.value = '';
        elements.questionTemplate.value = '';
        elements.answerTemplate.value = '';
        elements.paramsContainer.innerHTML = '';
        state.currentTemplateId = null;
        state.isEditing = false;
    }

    function updateParameters() {
        const question = elements.questionTemplate.value;
        const answer = elements.answerTemplate.value;
        elements.paramsContainer.innerHTML = '';

        const params = new Set();
        const regex = /\{([A-Za-z]+)\}/g;
        let match;
        
        while ((match = regex.exec(question))) params.add(match[1]);
        while ((match = regex.exec(answer))) params.add(match[1]);

        params.forEach(param => {
            const group = document.createElement('div');
            group.className = 'param-group';
            group.innerHTML = `
                <h4>Параметр ${param}</h4>
                <div class="param-row">
                    <label>Тип:
                        <select class="param-type">
                            <option value="int">Целое число</option>
                            <option value="float">Дробное число</option>
                        </select>
                    </label>
                    <label>Минимум: <input type="number" class="param-min" value="1" min="0"></label>
                    <label>Максимум: <input type="number" class="param-max" value="10" min="1"></label>
                </div>
                <div class="param-constraints">
                    <button class="btn btn-small add-constraint">+ Добавить условие</button>
                </div>
            `;
            elements.paramsContainer.appendChild(group);
        });

        // Обработчик для добавления условий
        document.querySelectorAll('.add-constraint').forEach(btn => {
            btn.addEventListener('click', function() {
                const constraintsContainer = this.closest('.param-group').querySelector('.param-constraints');
                const constraintDiv = document.createElement('div');
                constraintDiv.className = 'constraint';
                constraintDiv.innerHTML = `
                    <select class="constraint-type">
                        <option value="multiple_of">Кратно</option>
                        <option value="greater_than">Больше чем</option>
                        <option value="less_than">Меньше чем</option>
                        <option value="equals">Равно</option>
                    </select>
                    <input type="text" class="constraint-value" placeholder="Значение или параметр">
                    <button class="btn-icon remove-constraint">×</button>
                `;
                constraintsContainer.insertBefore(constraintDiv, this);
            });
        });
    }

    async function loadTemplateData(templateId) {
        try {
            const response = await fetch(`${API_BASE}/templates/${templateId}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Ошибка загрузки шаблона');
            }
            
            return data.template;
        } catch (error) {
            console.error('Ошибка загрузки шаблона:', error);
            throw error;
        }
    }

    function renderTemplateParams(template) {
        elements.paramsContainer.innerHTML = '';
        const params = JSON.parse(template.parameters);
        
        for (const [param, config] of Object.entries(params)) {
            const group = document.createElement('div');
            group.className = 'param-group';
            
            // Рендерим основные параметры
            group.innerHTML = `
                <h4>Параметр ${param}</h4>
                <div class="param-row">
                    <label>Тип:
                        <select class="param-type">
                            <option value="int" ${config.type === 'int' ? 'selected' : ''}>Целое число</option>
                            <option value="float" ${config.type === 'float' ? 'selected' : ''}>Дробное число</option>
                        </select>
                    </label>
                    <label>Минимум: <input type="number" class="param-min" value="${config.min}" min="0"></label>
                    <label>Максимум: <input type="number" class="param-max" value="${config.max}" min="1"></label>
                </div>
                <div class="param-constraints">
                    ${renderConstraints(config.constraints || [])}
                    <button class="btn btn-small add-constraint">+ Добавить условие</button>
                </div>
            `;
            
            elements.paramsContainer.appendChild(group);
        }
    }

    function renderConstraints(constraints) {
        return constraints.map(constraint => `
            <div class="constraint">
                <select class="constraint-type">
                    <option value="multiple_of" ${constraint.type === 'multiple_of' ? 'selected' : ''}>Кратно</option>
                    <option value="greater_than" ${constraint.type === 'greater_than' ? 'selected' : ''}>Больше чем</option>
                    <option value="less_than" ${constraint.type === 'less_than' ? 'selected' : ''}>Меньше чем</option>
                    <option value="equals" ${constraint.type === 'equals' ? 'selected' : ''}>Равно</option>
                </select>
                <input type="text" class="constraint-value" value="${constraint.value || constraint.param || ''}">
                <button class="btn-icon remove-constraint">×</button>
            </div>
        `).join('');
    }

    async function saveTemplate() {
        const name = elements.templateName.value.trim();
        const question = elements.questionTemplate.value.trim();
        const answer = elements.answerTemplate.value.trim();

        if (!name || !question || !answer) {
            alert('Заполните все обязательные поля');
            return;
        }

        // Собираем параметры
        const params = {};
        const paramGroups = elements.paramsContainer.querySelectorAll('.param-group');
        
        for (const group of paramGroups) {
            const param = group.querySelector('h4').textContent.replace('Параметр ', '');
            const type = group.querySelector('.param-type').value;
            const min = parseInt(group.querySelector('.param-min').value);
            const max = parseInt(group.querySelector('.param-max').value);
            
            if (min >= max) {
                alert(`Для параметра ${param} максимум должен быть больше минимума`);
                return;
            }
            
            // Собираем ограничения
            const constraints = [];
            group.querySelectorAll('.constraint').forEach(constraintEl => {
                constraints.push({
                    type: constraintEl.querySelector('.constraint-type').value,
                    value: constraintEl.querySelector('.constraint-value').value
                });
            });
            
            params[param] = { 
                type,
                min, 
                max,
                constraints: constraints.length ? constraints : undefined
            };
        }

        try {
            const url = state.isEditing 
                ? `${API_BASE}/templates/${state.currentTemplateId}`
                : `${API_BASE}/templates`;

            const method = 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    textbook_id: textbookId,
                    name: name,
                    question_template: question,
                    answer_template: answer,
                    parameters: params
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка сервера');
            }

            alert(TEXTS.saveSuccess);
            resetForm();
            toggleForm(false);
            loadTemplates();
        } catch (error) {
            console.error('Ошибка сохранения:', error);
            alert(`Ошибка: ${error.message}`);
        }
    }

    async function loadTemplates() {
        try {
            const response = await fetch(`/api/textbooks/${textbookId}/templates`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Ошибка загрузки шаблонов');
            }
            
            renderTemplates(data.templates);
        } catch (error) {
            console.error('Ошибка загрузки шаблонов:', error);
            elements.templatesList.innerHTML = `
                <div class="error">Ошибка загрузки: ${error.message}</div>
            `;
        }
    }

    function renderTemplates(templates) {
        elements.templatesList.innerHTML = templates.length 
            ? templates.map((template, index) => `
                <div class="template-card" data-id="${template.id}">
                    <div class="template-header">
                        <h3>№${index + 1}: ${template.name}</h3>
                        <div class="template-actions">
                            <button class="btn-icon edit-btn">✏️</button>
                            <button class="btn-icon delete-btn">🗑️</button>
                        </div>
                    </div>
                    <div class="template-content">
                        <p><strong>Вопрос:</strong> ${template.question_template}</p>
                        <p><strong>Ответ:</strong> ${template.answer_template}</p>
                    </div>
                </div>
            `).join('')
            : '<p class="no-templates">Нет созданных шаблонов</p>';
    }

    async function deleteTemplate(templateId) {
        if (!confirm(TEXTS.deleteConfirm)) return;

        try {
            const response = await fetch(`${API_BASE}/templates/${templateId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка удаления');
            }

            alert(TEXTS.deleteSuccess);
            loadTemplates();
        } catch (error) {
            console.error('Ошибка удаления:', error);
            alert(`Ошибка удаления: ${error.message}`);
        }
    }

    async function setupEditTemplate(templateId) {
        try {
            const template = await loadTemplateData(templateId);
            
            state.currentTemplateId = templateId;
            state.isEditing = true;
            
            // Заполняем форму данными
            elements.templateName.value = template.name;
            elements.questionTemplate.value = template.question_template;
            elements.answerTemplate.value = template.answer_template;
            
            // Рендерим параметры
            renderTemplateParams(template);
            
            toggleForm(true);
        } catch (error) {
            alert(`Ошибка загрузки шаблона: ${error.message}`);
        }
    }

    // ===== ИНИЦИАЛИЗАЦИЯ =====
    function initEventListeners() {
        elements.showFormBtn.addEventListener('click', () => {
            resetForm();
            toggleForm(true);
        });

        elements.cancelBtn.addEventListener('click', () => toggleForm(false));
        elements.saveBtn.addEventListener('click', saveTemplate);
        elements.questionTemplate.addEventListener('input', updateParameters);
        elements.answerTemplate.addEventListener('input', updateParameters);

        // Делегирование событий для списка
        elements.templatesList.addEventListener('click', (e) => {
            const card = e.target.closest('.template-card');
            if (!card) return;

            const templateId = parseInt(card.dataset.id);

            if (e.target.classList.contains('delete-btn')) {
                deleteTemplate(templateId);
            } else if (e.target.classList.contains('edit-btn')) {
                setupEditTemplate(templateId);
            }
        });
    }

    // Запуск приложения
    function init() {
        initEventListeners();
        loadTemplates();
    }

    init();
});