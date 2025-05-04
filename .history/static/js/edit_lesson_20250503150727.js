document.addEventListener('DOMContentLoaded', function() {
    // Текущий урок и задание
    const lessonId = window.location.pathname.split('/').pop();
    let currentTaskId = null;
    let tasks = [];
    let currentTaskIndex = 0;

    // Инициализация редактора
    initTaskEditor();
    loadLessonData();

    // Загрузка данных урока
    async function loadLessonData() {
        try {
            const response = await fetch(`/api/lessons/${lessonId}/tasks`);
            if (!response.ok) throw new Error('Ошибка загрузки данных');
            
            tasks = await response.json();
            if (tasks.length > 0) {
                currentTaskId = tasks[0].id;
                loadTaskEditor(tasks[0]);
            } else {
                createNewTask();
            }
            renderTaskList();
            updateTaskCounter();
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось загрузить данные урока');
        }
    }

    // Инициализация редактора задания
    function initTaskEditor() {
        // Обработчики для подсказок
        document.querySelector('.formula-help-btn').addEventListener('click', showFormulaHelp);
        
        // Автоопределение параметров
        document.getElementById('autoDetectParamsBtn').addEventListener('click', autoDetectParams);
        
        // Генерация примеров
        document.getElementById('generateExamplesBtn').addEventListener('click', generateExamples);
        
        // Добавление параметра
        document.getElementById('addParamBtn').addEventListener('click', addNewParameter);
        
        // Сохранение задания
        document.getElementById('saveTaskBtn').addEventListener('click', saveCurrentTask);
        
        // Новое задание
        document.getElementById('addBlankTask').addEventListener('click', createNewTask);
        
        // Удаление задания
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-task-btn') || 
                e.target.classList.contains('remove-param-btn')) {
                e.stopPropagation();
                if (confirm('Удалить этот элемент?')) {
                    if (e.target.classList.contains('remove-task-btn')) {
                        deleteTask(e.target.closest('.task-item').dataset.taskId);
                    } else {
                        e.target.closest('.param-card').remove();
                    }
                }
            }
        });
    }

    document.getElementById('saveAllBtn').addEventListener('click', async function() {
        const lessonId = window.location.pathname.split('/').pop();
        
        try {
            // Показываем загрузку
            this.disabled = true;
            this.textContent = 'Сохранение...';
            
            // Подготовка данных
            const tasksData = tasks.map(task => ({
                id: task.id.startsWith('new-') ? null : task.id,
                question: task.question,
                answer: task.answer_formula,
                params: task.params || {}
            }));
    
            // Отправка на сервер
            const response = await fetch(`/api/lessons/${lessonId}/tasks/batch`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken() // Если используете CSRF
                },
                body: JSON.stringify({ tasks: tasksData })
            });
    
            if (!response.ok) {
                throw new Error(await response.text());
            }
    
            const result = await response.json();
            alert(result.message || 'Урок успешно сохранён!');
            
            // Обновляем ID новых заданий
            if (result.updatedTasks) {
                tasks.forEach((task, index) => {
                    if (task.id.startsWith('new-') && result.updatedTasks[index]) {
                        task.id = result.updatedTasks[index];
                    }
                });
            }
        } catch (error) {
            console.error('Ошибка сохранения:', error);
            alert('Ошибка сохранения: ' + error.message);
        } finally {
            this.disabled = false;
            this.textContent = 'Сохранить весь урок';
        }
    });

    // Загрузка задания в редактор
    function loadTaskEditor(task) {
        currentTaskId = task.id;
        currentTaskIndex = tasks.findIndex(t => t.id === task.id);
        
        document.getElementById('taskTemplate').value = task.question || '';
        document.getElementById('answerFormula').value = task.answer_formula || '';
        
        // Загрузка параметров
        if (task.params && Object.keys(task.params).length > 0) {
            renderParamControls(task.params);
        } else if (task.question) {
            autoDetectParams();
        }
        
        // Генерация примеров
        if (task.question && task.answer_formula) {
            generateExamples();
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
        document.getElementById('taskTemplate').focus();
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

    // Отрисовка списка заданий
    function renderTaskList() {
        const container = document.getElementById('tasksContainer');
        container.innerHTML = '';
        
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
            
            container.appendChild(taskEl);
        });
    }

    // Обновление счетчика заданий
    function updateTaskCounter() {
        document.getElementById('currentTaskNum').textContent = currentTaskIndex + 1;
    }

    // Подсказка по формулам
    function showFormulaHelp() {
        alert(`Формула ответа должна использовать те же параметры, что и в шаблоне.\n\nПримеры:
1. Для "{A} + {B}" → "A + B"
2. Для "{A}x + {B} = {C}" → "(C - B)/A"
3. Для площади круга "π{R}^2" → "3.14*R*R"
4. Для квадратного уравнения "{A}x^2 + {B}x + {C} = 0" → "(-B + sqrt(B^2 - 4*A*C))/(2*A)"
        
Можно использовать: + - * / ^ sqrt() abs()`);
    }

    // Автоопределение параметров
    function autoDetectParams() {
        const template = document.getElementById('taskTemplate').value;
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
        const container = document.getElementById('paramControls');
        container.innerHTML = '';
        
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
            container.appendChild(paramCard);
        }
    }

    // Добавление нового параметра
    function addNewParameter() {
        const paramName = prompt('Введите имя параметра (одна буква):', 'D');
        if (!paramName || !/^[A-Za-z]$/.test(paramName)) {
            alert('Имя параметра должно быть одной буквой!');
            return;
        }
        
        const container = document.getElementById('paramControls');
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
        container.appendChild(paramCard);
    }

    // Генерация примеров
    function generateExamples() {
        const template = document.getElementById('taskTemplate').value;
        const formula = document.getElementById('answerFormula').value;
        const count = parseInt(document.getElementById('examplesCount').value);
        
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
        for (let i = 0; i < count; i++) {
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
        const container = document.getElementById('taskExamples');
        container.innerHTML = '';
        
        examples.forEach((ex, index) => {
            const exampleCard = document.createElement('div');
            exampleCard.className = 'example-card';
            exampleCard.innerHTML = `
                <div class="example-question">${index + 1}. ${ex.question}</div>
                <div class="example-answer">Ответ: ${ex.answer}</div>
            `;
            container.appendChild(exampleCard);
        });
    }


    function validateTaskParams(template) {
        const params = template.match(/\{([^}]+)\}/g) || [];
        const normalized = params.map(p => p.toUpperCase().replace(/\{|\}/g, ''));
        const duplicates = normalized.filter((p, i) => normalized.indexOf(p) !== i);
        
        if (duplicates.length > 0) {
            throw new Error(`Параметры должны быть уникальными (без учета регистра). 
                Найдены дубликаты: ${duplicates.join(', ')}`);
        }
        
        // Проверка допустимых символов
        const invalid = normalized.filter(p => !/^[A-Za-z]+$/.test(p));
        if (invalid.length > 0) {
            throw new Error(`Недопустимые имена параметров: ${invalid.join(', ')}. 
                Используйте только буквы A-Z.`);
        }
        
        return normalized;
    }

    // Сохранение текущего задания
    async function saveCurrentTask() {
        const template = document.getElementById('taskTemplate').value;
        const formula = document.getElementById('answerFormula').value;
        
        if (!template) {
            alert('Введите шаблон задания');
            return;
        }
        
        const taskData = {
            id: currentTaskId,
            question: template,
            answer: formula  // Используем 'answer' вместо 'answer_formula'
        };
        
        try {
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
            if (data.success) {
                if (data.taskId) {
                    currentTaskId = data.taskId;
                    // Обновляем ID в локальном хранилище
                    const taskIndex = tasks.findIndex(t => t.id === currentTaskId);
                    if (taskIndex !== -1) {
                        tasks[taskIndex].id = data.taskId;
                    }
                }
                alert('Задание успешно сохранено!');
                renderTaskList();
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось сохранить задание');
        }
    }
});