document.addEventListener('DOMContentLoaded', function() {
    const textbookId = {{ textbook.id }};
    const taskFormContainer = document.getElementById('taskFormContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const cancelTaskBtn = document.getElementById('cancelTaskBtn');
    
    // Проверяем, что элементы существуют
    if (!addTaskBtn || !taskFormContainer) {
        console.error('Не найдены необходимые элементы на странице');
        return;
    }

    // Показать форму добавления
    addTaskBtn.addEventListener('click', function() {
        console.log('Кнопка "Добавить шаблон" нажата'); // Добавим лог для отладки
        resetForm();
        taskFormContainer.classList.remove('hidden');
        document.getElementById('formTitle').textContent = 'Новый шаблон задания';
    });

    // Скрыть форму
    cancelTaskBtn.addEventListener('click', function() {
        taskFormContainer.classList.add('hidden');
    });

    // Сброс формы
    function resetForm() {
        document.getElementById('templateName').value = '';
        document.getElementById('questionTemplate').value = '';
        document.getElementById('answerTemplate').value = '';
        document.getElementById('parametersContainer').innerHTML = '';
    }

    // Добавим обработку изменений в полях вопроса и ответа
    document.getElementById('questionTemplate')?.addEventListener('input', updateParameters);
    document.getElementById('answerTemplate')?.addEventListener('input', updateParameters);

    // Функция обновления параметров
    function updateParameters() {
        const question = document.getElementById('questionTemplate').value;
        const answer = document.getElementById('answerTemplate').value;
        const paramsContainer = document.getElementById('parametersContainer');
        
        // Очищаем контейнер
        paramsContainer.innerHTML = '';

        // Находим все параметры в формате {A}, {B} и т.д.
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
});