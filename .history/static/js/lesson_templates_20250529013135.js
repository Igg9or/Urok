document.addEventListener('DOMContentLoaded', function() {
    const API_BASE = '/api';
    const templateForm = document.getElementById('templateForm');
    const textbookSelect = document.getElementById('textbookSelect');
    const templatesList = document.getElementById('templatesList');

    // Показать/скрыть форму
    document.getElementById('showFormBtn').addEventListener('click', function() {
        templateForm.classList.remove('hidden');
    });

    document.getElementById('cancelBtn').addEventListener('click', function() {
        templateForm.classList.add('hidden');
    });

    // Загрузка шаблонов из учебника
    textbookSelect.addEventListener('change', function() {
        const textbookId = this.value;
        if (!textbookId) return;
        
        fetch(`${API_BASE}/textbooks/${textbookId}/templates`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderTemplates(data.templates);
                }
            });
    });

    // Сохранение шаблона
    document.getElementById('saveTemplateBtn').addEventListener('click', function() {
        const name = document.getElementById('templateName').value.trim();
        const question = document.getElementById('questionTemplate').value.trim();
        const answer = document.getElementById('answerTemplate').value.trim();
        
        if (!name || !question || !answer) {
            alert('Заполните все обязательные поля');
            return;
        }
        
        // Собираем параметры (упрощенная версия)
        const params = {};
        const paramMatches = [...new Set([...question.matchAll(/\{([A-Za-z]+)\}/g), ...answer.matchAll(/\{([A-Za-z]+)\}/g)])];
        paramMatches.forEach(match => {
            params[match[1]] = { min: 1, max: 10 }; // Упрощенные параметры
        });

        fetch(`${API_BASE}/lesson_templates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                question_template: question,
                answer_template: answer,
                parameters: params
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Шаблон сохранен');
                templateForm.classList.add('hidden');
                loadLessonTemplates();
            }
        });
    });

    // Загрузка шаблонов уроков
    function loadLessonTemplates() {
        fetch(`${API_BASE}/lesson_templates`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderTemplates(data.templates);
                }
            });
    }

    // Отображение шаблонов
    function renderTemplates(templates) {
        templatesList.innerHTML = templates.map(template => `
            <div class="template-card" data-id="${template.id}">
                <h3>${template.name}</h3>
                <p>${template.question_template}</p>
                <div class="template-actions">
                    <button class="btn btn-small use-template">Использовать</button>
                </div>
            </div>
        `).join('');
    }

    // Инициализация
    loadLessonTemplates();
});