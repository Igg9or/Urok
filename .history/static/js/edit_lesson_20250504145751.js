document.addEventListener('DOMContentLoaded', function() {
    // Текущий урок
    const lessonId = window.location.pathname.split('/').pop();
    let currentTaskId = null;
    let tasks = [];

    // Инициализация
    initTaskEditor();
    loadTasks();

    // Загрузка заданий урока
    async function loadTasks() {
        try {
            const response = await fetch(`/api/lessons/${lessonId}/tasks`);
            tasks = await response.json();
            renderTaskList();
        } catch (error) {
            console.error('Ошибка загрузки заданий:', error);
        }
    }

    // Рендер списка заданий
    function renderTaskList() {
        const container = document.getElementById('tasksContainer');
        container.innerHTML = '';
        
        tasks.forEach(task => {
            const taskEl = document.createElement('div');
            taskEl.className = 'task-item';
            taskEl.dataset.taskId = task.id;
            taskEl.draggable = true;
            taskEl.innerHTML = `
                <div class="task-preview">${task.question.substring(0, 50)}${task.question.length > 50 ? '...' : ''}</div>
                <button class="btn-remove-task">×</button>
            `;
            container.appendChild(taskEl);
        });
        
        // Назначение обработчиков
        document.querySelectorAll('.task-item').forEach(item => {
            item.addEventListener('click', () => loadTaskEditor(item.dataset.taskId));
        });

        // Удаление задания
        document.querySelectorAll('.btn-remove-task').forEach(button => {
            button.addEventListener('click', (event) => {
                const taskId = event.target.closest('.task-item').dataset.taskId;
                deleteTask(taskId);
            });
        });
    }

    // Загрузка задания в редактор
    function loadTaskEditor(taskId) {
        currentTaskId = taskId;
        const task = tasks.find(t => t.id == taskId);
        
        if (task) {
            document.getElementById('taskTemplate').value = task.question;
            document.getElementById('answerFormula').value = task.answer_formula;
            
            // Загрузка параметров
            renderParamControls(task.params);
            
            // Генерация примеров
            generateTaskExamples(task);
        }
    }

    // Работа с параметрами
    function renderParamControls(params) {
        const container = document.getElementById('paramControls');
        container.innerHTML = '';
        
        for (const [param, config] of Object.entries(params)) {
            const paramRow = document.createElement('div');
            paramRow.className = 'param-row';
            paramRow.innerHTML = `
                <label>${param}:</label>
                <select class="param-type">
                    <option value="int" ${config.type === 'int' ? 'selected' : ''}>Целое</option>
                    <option value="float" ${config.type === 'float' ? 'selected' : ''}>Дробное</option>
                </select>
                <input type="number" class="param-min" value="${config.min}" placeholder="Мин">
                <input type="number" class="param-max" value="${config.max}" placeholder="Макс">
                <button class="btn-remove-param">×</button>
            `;
            container.appendChild(paramRow);
        }
    }

    // Генерация примеров
    async function generateTaskExamples(task) {
        try {
            const response = await fetch('/api/generate-examples', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template: task.question,
                    params: task.params,
                    count: 3
                })
            });
            
            const examples = await response.json();
            renderExamples(examples);
        } catch (error) {
            console.error('Ошибка генерации примеров:', error);
        }
    }

    // Сохранение урока
    document.getElementById('saveLessonBtn').addEventListener('click', async function() {
        const lessonData = {
            title: document.getElementById('lessonTitle').value,
            tasks: tasks.map(task => ({
                id: task.id,
                question: task.question,
                answer_formula: task.answer_formula,
                params: task.params
            }))
        };
        
        try {
            const response = await fetch(`/api/lessons/${lessonId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(lessonData)
            });
            
            if (response.ok) {
                alert('Урок успешно сохранен!');
            }
        } catch (error) {
            console.error('Ошибка сохранения:', error);
        }
    });

    // Удаление задания
    async function deleteTask(taskId) {
        try {
            const response = await fetch(`/teacher/delete_task/${taskId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                tasks = tasks.filter(task => task.id !== parseInt(taskId));
                renderTaskList();  // Обновляем список заданий
            } else {
                alert('Ошибка удаления задания');
            }
        } catch (error) {
            console.error('Ошибка удаления задания:', error);
        }
    }
});

// Вспомогательные функции
function extractParamsFromTemplate(template) {
    const regex = /\{([A-Za-z]+)\}/g;
    const params = new Set();
    let match;
    
    while ((match = regex.exec(template)) !== null) {
        params.add(match[1]);
    }
    
    return Array.from(params);
}
