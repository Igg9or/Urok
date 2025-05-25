document.addEventListener('DOMContentLoaded', function() {
    const textbookId = {{ textbook.id }};
    const tasksList = document.getElementById('tasksList');
    const taskFormContainer = document.getElementById('taskFormContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const cancelTaskBtn = document.getElementById('cancelTaskBtn');
    const saveTaskBtn = document.getElementById('saveTaskBtn');
    let currentTemplateId = null;

    // Показать форму добавления
    addTaskBtn.addEventListener('click', function() {
        currentTemplateId = null;
        document.getElementById('formTitle').textContent = 'Новый шаблон задания';
        resetForm();
        taskFormContainer.classList.remove('hidden');
    });

    // Скрыть форму
    cancelTaskBtn.addEventListener('click', function() {
        taskFormContainer.classList.add('hidden');
    });

    // Обработка сохранения
    saveTaskBtn.addEventListener('click', saveTemplate);

    // Обработка кликов по карточкам заданий
    tasksList.addEventListener('click', function(e) {
        const taskCard = e.target.closest('.task-card');
        if (!taskCard) return;

        if (e.target.classList.contains('edit-task')) {
            editTemplate(taskCard);
        } else if (e.target.classList.contains('delete-task')) {
            deleteTemplate(taskCard);
        }
    });

    // Сброс формы
    function resetForm() {
        document.getElementById('templateName').value = '';
        document.getElementById('questionTemplate').value = '';
        document.getElementById('answerTemplate').value = '';
        document.getElementById('parametersContainer').innerHTML = '';
    }

    // Редактирование шаблона
    function editTemplate(taskCard) {
        currentTemplateId = taskCard.dataset.templateId;
        const question = taskCard.querySelector('.question-preview').textContent;
        const answer = taskCard.querySelector('.answer-preview').textContent;

        document.getElementById('formTitle').textContent = 'Редактирование шаблона';
        document.getElementById('templateName').value = taskCard.querySelector('h3').textContent.replace('Задание №', '');
        document.getElementById('questionTemplate').value = question;
        document.getElementById('answerTemplate').value = answer;
        
        updateParameters();
        taskFormContainer.classList.remove('hidden');
    }

    // Обновление параметров
    function updateParameters() {
        const question = document.getElementById('questionTemplate').value;
        const answer = document.getElementById('answerTemplate').value;
        const paramsContainer = document.getElementById('parametersContainer');
        const params = new Set();

        // Находим все параметры
        const paramRegex = /\{([A-Za-z]+)\}/g;
        let match;
        
        while ((match = paramRegex.exec(question))) {
            params.add(match[1]);
        }
        
        while ((match = paramRegex.exec(answer))) {
            params.add(match[1]);
        }

        // Очищаем контейнер
        paramsContainer.innerHTML = '';

        // Добавляем поля для каждого параметра
        params.forEach(param => {
            const paramGroup = document.createElement('div');
            paramGroup.className = 'param-group';
            paramGroup.innerHTML = `
                <h4>Параметр ${param}</h4>
                <div class="param-control">
                    <label>Минимум:</label>
                    <input type="number" class="param-min" value="1">
                </div>
                <div class="param-control">
                    <label>Максимум:</label>
                    <input type="number" class="param-max" value="10">
                </div>
            `;
            paramsContainer.appendChild(paramGroup);
        });
    }

    // Сохранение шаблона
    function saveTemplate() {
        const name = document.getElementById('templateName').value.trim();
        const question = document.getElementById('questionTemplate').value.trim();
        const answer = document.getElementById('answerTemplate').value.trim();

        if (!name || !question || !answer) {
            alert('Заполните все обязательные поля');
            return;
        }

        // Собираем параметры
        const params = {};
        document.querySelectorAll('.param-group').forEach(group => {
            const param = group.querySelector('h4').textContent.replace('Параметр ', '');
            const min = parseInt(group.querySelector('.param-min').value);
            const max = parseInt(group.querySelector('.param-max').value);
            
            if (min >= max) {
                alert(`Для параметра ${param} максимум должен быть больше минимума`);
                return;
            }
            
            params[param] = { min, max };
        });

        const url = currentTemplateId 
            ? `/teacher/update_task_template/${currentTemplateId}`
            : '/teacher/add_task_template';

        fetch(url, {
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
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert(data.error || 'Ошибка сохранения шаблона');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при сохранении шаблона');
        });
    }

    // Удаление шаблона
    function deleteTemplate(taskCard) {
        if (!confirm('Удалить этот шаблон задания?')) return;

        const templateId = taskCard.dataset.templateId;
        
        fetch(`/teacher/delete_task_template/${templateId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                taskCard.remove();
                // Обновляем нумерацию
                document.querySelectorAll('.task-card').forEach((card, index) => {
                    card.querySelector('h3').textContent = `Задание №${index + 1}`;
                });
            } else {
                alert(data.error || 'Ошибка удаления шаблона');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при удалении шаблона');
        });
    }

    // Обновление параметров при изменении полей
    document.getElementById('questionTemplate').addEventListener('input', updateParameters);
    document.getElementById('answerTemplate').addEventListener('input', updateParameters);
});