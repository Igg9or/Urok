document.addEventListener('DOMContentLoaded', function() {
    console.log('textbook_tasks.js loaded'); // Отладочное сообщение

    // Основные элементы
    const showFormBtn = document.getElementById('showFormBtn');
    const taskForm = document.getElementById('taskForm');
    const cancelBtn = document.getElementById('cancelBtn');
    const saveBtn = document.getElementById('saveTemplateBtn');
    const templatesList = document.getElementById('templatesList');

    // Проверка существования элементов
    if (!showFormBtn || !taskForm) {
        console.error('Required elements not found');
        return;
    }

    // ===== ОСНОВНЫЕ ФУНКЦИИ =====

    // Показать/скрыть форму
    function toggleForm(show = true) {
        taskForm.classList.toggle('hidden', !show);
        if (show) {
            resetForm();
            document.querySelector('#taskForm h3').textContent = 'Новый шаблон задания';
        }
    }

    // Сброс формы
    function resetForm() {
        document.getElementById('templateName').value = '';
        document.getElementById('questionTemplate').value = '';
        document.getElementById('answerTemplate').value = '';
        document.getElementById('paramsContainer').innerHTML = '';
    }

    // Обновление параметров
    function updateParameters() {
        const question = document.getElementById('questionTemplate').value;
        const answer = document.getElementById('answerTemplate').value;
        const container = document.getElementById('paramsContainer');
        
        container.innerHTML = '';

        // Находим все параметры {A}, {B} и т.д.
        const params = new Set();
        const regex = /\{([A-Za-z]+)\}/g;
        let match;
        
        while ((match = regex.exec(question))) params.add(match[1]);
        while ((match = regex.exec(answer))) params.add(match[1]);

        // Добавляем поля для параметров
        params.forEach(param => {
            const group = document.createElement('div');
            group.className = 'param-group';
            group.innerHTML = `
                <h4>Параметр ${param}</h4>
                <div class="param-row">
                    <label>Минимум: <input type="number" class="param-min" value="1"></label>
                    <label>Максимум: <input type="number" class="param-max" value="10"></label>
                </div>
            `;
            container.appendChild(group);
        });
    }

    // ===== ОБРАБОТЧИКИ СОБЫТИЙ =====

    // Показать форму
    showFormBtn.addEventListener('click', () => {
        console.log('Add button clicked');
        toggleForm(true);
    });

    // Скрыть форму
    cancelBtn.addEventListener('click', () => toggleForm(false));

    // Изменение полей вопроса/ответа
    document.getElementById('questionTemplate').addEventListener('input', updateParameters);
    document.getElementById('answerTemplate').addEventListener('input', updateParameters);

    // Сохранение шаблона
    saveBtn.addEventListener('click', function() {
        const name = document.getElementById('templateName').value.trim();
        const question = document.getElementById('questionTemplate').value.trim();
        const answer = document.getElementById('answerTemplate').value.trim();

        if (!name || !question || !answer) {
            alert('Заполните все поля!');
            return;
        }

        console.log('Saving template:', {name, question, answer});
        // Здесь будет код отправки на сервер
        alert('Шаблон сохранен!');
        toggleForm(false);
        // В реальном коде здесь нужно обновлять список шаблонов
    });

    // Делегирование событий для кнопок в списке
    templatesList.addEventListener('click', function(e) {
        const card = e.target.closest('.template-card');
        if (!card) return;

        if (e.target.classList.contains('delete-btn')) {
            if (confirm('Удалить этот шаблон?')) {
                console.log('Deleting template:', card.dataset.id);
                card.remove();
            }
        }
        else if (e.target.classList.contains('edit-btn')) {
            console.log('Editing template:', card.dataset.id);
            // Здесь будет код заполнения формы для редактирования
            toggleForm(true);
        }
    });

    // Инициализация
    console.log('Script initialized');
});