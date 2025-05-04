document.addEventListener('DOMContentLoaded', function() {
    // Конфигурация API
    const API_URL = `/api/lessons/${LESSON_ID}/tasks`;
    
    // Состояние приложения
    const state = {
        currentTaskId: null,
        tasks: [],
        currentTaskIndex: 0
    };

    // Инициализация приложения
    async function init() {
        try {
            await loadLessonData();
            setupEventListeners();
        } catch (error) {
            console.error('Initialization error:', error);
            showError('Не удалось инициализировать редактор');
        }
    }

    // Загрузка данных урока
    async function loadLessonData() {
        try {
            const response = await fetch(API_URL);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!Array.isArray(data)) {
                throw new Error('Invalid data format received from server');
            }
            
            state.tasks = data;
            
            if (state.tasks.length > 0) {
                state.currentTaskId = state.tasks[0].id;
                state.currentTaskIndex = 0;
                loadTaskEditor(state.tasks[0]);
            } else {
                createNewTask();
            }
            
            renderTaskList();
            updateTaskCounter();
        } catch (error) {
            console.error('Failed to load lesson data:', error);
            showError('Не удалось загрузить данные урока. Пожалуйста, обновите страницу.');
            throw error;
        }
    }

    // Показ ошибок
    function showError(message) {
        alert(message);
    }

    // Инициализация редактора задания
    function initTaskEditor() {
        // Обработчики событий
        elements.addTaskBtn.addEventListener('click', createNewTask);
        elements.addParamBtn.addEventListener('click', addNewParameter);
        elements.generateExamplesBtn.addEventListener('click', generateExamples);
        elements.saveTaskBtn.addEventListener('click', saveCurrentTask);
        elements.previewTaskBtn.addEventListener('click', previewTask);
    }

    // Загрузка задания в редактор
    function loadTaskEditor(task) {
        currentTaskId = task.id;
        currentTaskIndex = tasks.findIndex(t => t.id === task.id);
        
        elements.taskTemplate.value = task.question || '';
        elements.answerFormula.value = task.answer_formula || '';
        
        // Загрузка параметров
        if (task.params && Object.keys(task.params).length > 0) {
            renderParamControls(task.params);
        } else if (task.question) {
            autoDetectParams();
        }
        
        updateTaskCounter();
    }

    // Создание нового задания
    function createNewTask() {
        const newTask = {
            id: 'new-' + Date.now(),
            question: '',
            answer_formula: '',
            params: {}
        };
        
        tasks.push(newTask);
        currentTaskIndex = tasks.length - 1;
        currentTaskId = newTask.id;
        
        loadTaskEditor(newTask);
        renderTaskList();
        elements.taskTemplate.focus();
    }

    // Отрисовка списка заданий
    function renderTaskList() {
        elements.tasksList.innerHTML = '';
        
        tasks.forEach((task, index) => {
            const taskEl = document.createElement('div');
            taskEl.className = `task-item ${task.id === currentTaskId ? 'active' : ''}`;
            taskEl.dataset.taskId = task.id;
            taskEl.innerHTML = `
                <div class="task-preview">${index + 1}. ${task.question.substring(0, 50)}${task.question.length > 50 ? '...' : ''}</div>
                <button class="remove-task-btn">×</button>
            `;
            
            taskEl.addEventListener('click', () => {
                currentTaskIndex = index;
                loadTaskEditor(task);
            });
            
            // Обработчик удаления задания
            taskEl.querySelector('.remove-task-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm('Удалить это задание?')) {
                    deleteTask(task.id);
                }
            });
            
            elements.tasksList.appendChild(taskEl);
        });
    }

    // Удаление задания
    async function deleteTask(taskId) {
        try {
            // Если задание уже сохранено на сервере
            if (!taskId.startsWith('new-')) {
                const response = await fetch(`/api/tasks/${taskId}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) throw new Error('Ошибка удаления');
            }
            
            // Удаление из локального списка
            tasks = tasks.filter(task => task.id !== taskId);
            
            if (tasks.length === 0) {
                createNewTask();
            } else {
                currentTaskIndex = Math.min(currentTaskIndex, tasks.length - 1);
                loadTaskEditor(tasks[currentTaskIndex]);
            }
            
            renderTaskList();
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось удалить задание');
        }
    }

    // Обновление счетчика заданий
    function updateTaskCounter() {
        document.getElementById('currentTaskNum').textContent = currentTaskIndex + 1;
    }

    // Автоопределение параметров
    function autoDetectParams() {
        const template = elements.taskTemplate.value;
        const params = extractParamsFromTemplate(template);
        
        if (params.length === 0) {
            alert('Не найдено параметров в шаблоне. Используйте {A}, {B} и т.д.');
            return;
        }
        
        const paramsObj = {};
        params.forEach(param => {
            paramsObj[param] = {
                type: 'int',
                min: 1,
                max: 10,
                step: 1
            };
        });
        
        renderParamControls(paramsObj);
    }

    // Извлечение параметров из шаблона
    function extractParamsFromTemplate(template) {
        const regex = /\{([A-Za-z]+)\}/g;
        const params = new Set();
        let match;
        
        while ((match = regex.exec(template))) {
            params.add(match[1]);
        }
        
        return Array.from(params);
    }

    // Отрисовка параметров
    function renderParamControls(params) {
        elements.paramControls.innerHTML = '';
        
        for (const [name, config] of Object.entries(params)) {
            const paramCard = document.createElement('div');
            paramCard.className = 'param-card';
            paramCard.innerHTML = `
                <div class="param-header">
                    <span class="param-name">${name}</span>
                    <button class="remove-param-btn">×</button>
                </div>
                <div class="param-controls">
                    <label>Тип:</label>
                    <select class="param-type">
                        <option value="int" ${config.type === 'int' ? 'selected' : ''}>Целое</option>
                        <option value="float" ${config.type === 'float' ? 'selected' : ''}>Дробное</option>
                    </select>
                    
                    <label>Диапазон:</label>
                    <div class="range-inputs">
                        <input type="number" class="param-min" placeholder="Мин" value="${config.min}">
                        <span>до</span>
                        <input type="number" class="param-max" placeholder="Макс" value="${config.max}">
                    </div>
                    
                    <label>Шаг:</label>
                    <input type="number" class="param-step" placeholder="Шаг" value="${config.step}">
                </div>
            `;
            
            // Обработчик удаления параметра
            paramCard.querySelector('.remove-param-btn').addEventListener('click', function() {
                if (confirm(`Удалить параметр ${name}?`)) {
                    paramCard.remove();
                }
            });
            
            elements.paramControls.appendChild(paramCard);
        }
    }

    // Добавление нового параметра
    function addNewParameter() {
        const paramName = prompt('Введите имя параметра (одна буква):', 'D');
        if (!paramName || !/^[A-Za-z]$/.test(paramName)) {
            alert('Имя параметра должно быть одной буквой!');
            return;
        }
        
        const paramCard = document.createElement('div');
        paramCard.className = 'param-card';
        paramCard.innerHTML = `
            <div class="param-header">
                <span class="param-name">${paramName.toUpperCase()}</span>
                <button class="remove-param-btn">×</button>
            </div>
            <div class="param-controls">
                <label>Тип:</label>
                <select class="param-type">
                    <option value="int" selected>Целое</option>
                    <option value="float">Дробное</option>
                </select>
                
                <label>Диапазон:</label>
                <div class="range-inputs">
                    <input type="number" class="param-min" placeholder="Мин" value="1">
                    <span>до</span>
                    <input type="number" class="param-max" placeholder="Макс" value="10">
                </div>
                
                <label>Шаг:</label>
                <input type="number" class="param-step" placeholder="Шаг" value="1">
            </div>
        `;
        
        // Обработчик удаления параметра
        paramCard.querySelector('.remove-param-btn').addEventListener('click', function() {
            if (confirm(`Удалить параметр ${paramName.toUpperCase()}?`)) {
                paramCard.remove();
            }
        });
        
        elements.paramControls.appendChild(paramCard);
    }

    // Генерация примеров
    function generateExamples() {
        const template = elements.taskTemplate.value;
        const formula = elements.answerFormula.value;
        
        if (!template) {
            alert('Введите шаблон задания');
            return;
        }
        
        if (!formula) {
            alert('Введите формулу ответа');
            return;
        }
        
        const params = getCurrentParams();
        if (params.length === 0) {
            alert('Добавьте параметры для генерации примеров');
            return;
        }
        
        const examples = [];
        for (let i = 0; i < 3; i++) {
            const example = generateExample(template, formula, params);
            examples.push(example);
        }
        
        renderExamples(examples);
    }

    // Получение текущих параметров
    function getCurrentParams() {
        const params = [];
        document.querySelectorAll('.param-card').forEach(card => {
            const name = card.querySelector('.param-name').textContent;
            const type = card.querySelector('.param-type').value;
            const min = parseFloat(card.querySelector('.param-min').value) || 0;
            const max = parseFloat(card.querySelector('.param-max').value) || 10;
            const step = parseFloat(card.querySelector('.param-step').value) || 1;
            
            params.push({ name, type, min, max, step });
        });
        
        return params;
    }

    // Генерация одного примера
    function generateExample(template, formula, params) {
        const values = {};
        let question = template;
        
        // Генерация значений параметров
        params.forEach(param => {
            let value;
            if (param.type === 'int') {
                const steps = Math.floor((param.max - param.min) / param.step);
                const randomStep = Math.floor(Math.random() * (steps + 1));
                value = param.min + randomStep * param.step;
            } else {
                value = param.min + Math.random() * (param.max - param.min);
                value = Math.round(value * 100) / 100; // Округление до 2 знаков
            }
            
            values[param.name] = value;
            question = question.replace(new RegExp(`\\{${param.name}\\}`, 'g'), value);
        });
        
        // Вычисление ответа
        let answer;
        try {
            answer = evaluateFormula(formula, values);
        } catch (e) {
            answer = 'Ошибка в формуле';
        }
        
        return { question, answer };
    }

    // Вычисление формулы
    function evaluateFormula(formula, values) {
        // Замена параметров на значения
        let expr = formula;
        for (const [key, value] of Object.entries(values)) {
            expr = expr.replace(new RegExp(key, 'g'), value);
        }
        
        // Замена математических операций
        expr = expr.replace(/\^/g, '**');
        
        // Безопасное вычисление
        try {
            // eslint-disable-next-line no-new-func
            const result = new Function(`return ${expr}`)();
            return Number.isInteger(result) ? result : result.toFixed(2);
        } catch (e) {
            console.error('Ошибка вычисления:', e);
            return 'Ошибка';
        }
    }

    // Отрисовка примеров
    function renderExamples(examples) {
        elements.taskExamples.innerHTML = '';
        
        examples.forEach((ex, index) => {
            const exampleCard = document.createElement('div');
            exampleCard.className = 'example-card';
            exampleCard.innerHTML = `
                <div class="example-question">${index + 1}. ${ex.question}</div>
                <div class="example-answer">Ответ: ${ex.answer}</div>
            `;
            elements.taskExamples.appendChild(exampleCard);
        });
    }

    // Предпросмотр задания
    function previewTask() {
        generateExamples();
    }

    // Сохранение текущего задания
    async function saveCurrentTask() {
        const template = elements.taskTemplate.value;
        const formula = elements.answerFormula.value;
        
        if (!template) {
            alert('Введите шаблон задания');
            return;
        }
        
        if (!formula) {
            alert('Введите формулу ответа');
            return;
        }
        
        const params = {};
        document.querySelectorAll('.param-card').forEach(card => {
            const name = card.querySelector('.param-name').textContent;
            const type = card.querySelector('.param-type').value;
            const min = parseFloat(card.querySelector('.param-min').value) || 0;
            const max = parseFloat(card.querySelector('.param-max').value) || 10;
            const step = parseFloat(card.querySelector('.param-step').value) || 1;
            
            params[name] = { type, min, max, step };
        });
        
        const taskData = {
            id: currentTaskId,
            question: template,
            answer_formula: formula,
            params: params
        };
        
        try {
            // Обновляем локальные данные
            const taskIndex = tasks.findIndex(t => t.id === currentTaskId);
            if (taskIndex !== -1) {
                tasks[taskIndex] = taskData;
            }
            
            // Сохраняем на сервере
            const url = currentTaskId.startsWith('new-') ? 
                `/api/lessons/${lessonId}/tasks` : 
                `/api/tasks/${currentTaskId}`;
                
            const method = currentTaskId.startsWith('new-') ? 'POST' : 'PUT';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });
            
            if (!response.ok) throw new Error('Ошибка сохранения');
            
            const data = await response.json();
            if (data.success && data.taskId) {
                currentTaskId = data.taskId;
                tasks[taskIndex].id = data.taskId;
                alert('Задание успешно сохранено!');
                renderTaskList();
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось сохранить задание');
        }
    }
});