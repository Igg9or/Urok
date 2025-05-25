document.addEventListener('DOMContentLoaded', function() {
    console.log('textbook_tasks.js loaded'); // Отладочное сообщение

    // Основные элементы
    const textbookId = {{ textbook.id }};
    const addTaskBtn = document.getElementById('addTaskBtn');
    const taskFormContainer = document.getElementById('taskFormContainer');
    const cancelTaskBtn = document.getElementById('cancelTaskBtn');
    const saveTaskBtn = document.getElementById('saveTaskBtn');
    const templateNameInput = document.getElementById('templateName');
    const questionTemplateInput = document.getElementById('questionTemplate');
    const answerTemplateInput = document.getElementById('answerTemplate');
    const parametersContainer = document.getElementById('parametersContainer');
    
    // Проверка существования элементов
    if (!addTaskBtn || !taskFormContainer) {
        console.error('Required elements not found');
        return;
    }

    // Показать форму добавления
    addTaskBtn.addEventListener('click', function() {
        console.log('Add template button clicked');
        resetForm();
        taskFormContainer.classList.remove('hidden');
        document.getElementById('formTitle').textContent = 'Новый шаблон задания';
        document.body.scrollTop = document.body.scrollHeight; // Прокрутка к форме
    });

    // Скрыть форму
    cancelTaskBtn.addEventListener('click', function() {
        taskFormContainer.classList.add('hidden');
    });

    // Сброс формы
    function resetForm() {
        templateNameInput.value = '';
        questionTemplateInput.value = '';
        answerTemplateInput.value = '';
        parametersContainer.innerHTML = '';
    }

    // Обновление параметров при изменении полей
    questionTemplateInput.addEventListener('input', updateParameters);
    answerTemplateInput.addEventListener('input', updateParameters);

    // Функция обновления параметров
    function updateParameters() {
        const question = questionTemplateInput.value;
        const answer = answerTemplateInput.value;
        
        // Очищаем контейнер
        parametersContainer.innerHTML = '';

        // Находим все уникальные параметры
        const params = new Set();
        const paramRegex = /\{([A-Za-z]+)\}/g;
        let match;
        
        while ((match = paramRegex.exec(question))) {
            params.add(match[1]);
        }
        
        while ((match = paramRegex.exec(answer))) {
            params.add(match[1]);
        }

        // Добавляем поля для каждого параметра
        params.forEach(param => {
            const paramGroup = document.createElement('div');
            paramGroup.className = 'param-group';
            paramGroup.innerHTML = `
                <h4>Параметр ${param}</h4>
                <div class="param-control">
                    <label>Минимум:</label>
                    <input type="number" class="param-min" value="1" min="1">
                </div>
                <div class="param-control">
                    <label>Максимум:</label>
                    <input type="number" class="param-max" value="10" min="2">
                </div>
            `;
            parametersContainer.appendChild(paramGroup);
        });
    }

    // Сохранение шаблона
    saveTaskBtn.addEventListener('click', function() {
        const name = templateNameInput.value.trim();
        const question = questionTemplateInput.value.trim();
        const answer = answerTemplateInput.value.trim();

        if (!name || !question || !answer) {
            alert('Заполните все обязательные поля');
            return;
        }

        // Собираем параметры
        const params = {};
        const paramGroups = parametersContainer.querySelectorAll('.param-group');
        
        paramGroups.forEach(group => {
            const paramName = group.querySelector('h4').textContent.replace('Параметр ', '');
            const min = parseInt(group.querySelector('.param-min').value);
            const max = parseInt(group.querySelector('.param-max').value);
            
            if (min >= max) {
                alert(`Для параметра ${paramName} максимум должен быть больше минимума`);
                return;
            }
            
            params[paramName] = { min, max };
        });

        // Отправка данных
        fetch('/teacher/add_task_template', {
            method: 'POST',
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
        })
        .then(response => {
            if (!response.ok) throw new Error('Network error');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                window.location.reload(); // Перезагрузка страницы после сохранения
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при сохранении: ' + error.message);
        });
    });

    // Обработка кликов по существующим заданиям
    document.querySelectorAll('.edit-task').forEach(btn => {
        btn.addEventListener('click', function() {
            const taskCard = this.closest('.task-card');
            const templateId = taskCard.dataset.templateId;
            const question = taskCard.querySelector('.question-preview').textContent;
            const answer = taskCard.querySelector('.answer-preview').textContent;
            
            // Заполняем форму для редактирования
            templateNameInput.value = taskCard.querySelector('h3').textContent.replace('Задание №', '');
            questionTemplateInput.value = question;
            answerTemplateInput.value = answer;
            updateParameters();
            
            document.getElementById('formTitle').textContent = 'Редактирование шаблона';
            taskFormContainer.classList.remove('hidden');
            currentTemplateId = templateId;
        });
    });

    // Обработка удаления заданий
    document.querySelectorAll('.delete-task').forEach(btn => {
        btn.addEventListener('click', function() {
            if (confirm('Удалить этот шаблон задания?')) {
                const templateId = this.closest('.task-card').dataset.templateId;
                
                fetch(`/teacher/delete_task_template/${templateId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert('Ошибка удаления: ' + (data.error || ''));
                    }
                });
            }
        });
    });
});