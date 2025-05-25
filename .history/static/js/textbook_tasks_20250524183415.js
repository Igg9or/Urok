document.addEventListener('DOMContentLoaded', function() {
    const textbookId = {{ textbook.id }};
    const paramsContainer = document.getElementById('parametersContainer');
    const questionInput = document.getElementById('questionTemplate');
    const answerInput = document.getElementById('answerTemplate');
    
    // Обработка использования существующего шаблона
    document.querySelectorAll('.use-template').forEach(btn => {
        btn.addEventListener('click', function() {
            questionInput.value = this.dataset.question;
            answerInput.value = this.dataset.answer;
            updateParameters();
        });
    });
    
    // Обновление параметров при изменении вопроса
    questionInput.addEventListener('input', updateParameters);
    
    // Добавление параметров через кнопки
    document.querySelectorAll('.btn-math').forEach(btn => {
        btn.addEventListener('click', function() {
            const field = document.activeElement === answerInput ? answerInput : questionInput;
            const value = this.dataset.insert;
            const startPos = field.selectionStart;
            const endPos = field.selectionEnd;
            
            field.value = field.value.substring(0, startPos) + value + field.value.substring(endPos);
            field.focus();
            field.setSelectionRange(startPos + value.length, startPos + value.length);
            
            updateParameters();
        });
    });
    
    // Функция обновления списка параметров
    function updateParameters() {
        const question = questionInput.value;
        const answer = answerInput.value;
        const allParams = new Set();
        
        // Находим все параметры в вопросе и ответе
        const paramRegex = /\{([A-Z]+)\}/g;
        let match;
        
        while ((match = paramRegex.exec(question)) !== null) {
            allParams.add(match[1]);
        }
        
        while ((match = paramRegex.exec(answer)) !== null) {
            allParams.add(match[1]);
        }
        
        // Очищаем контейнер
        paramsContainer.innerHTML = '';
        
        // Добавляем поля для каждого параметра
        allParams.forEach(param => {
            const paramGroup = document.createElement('div');
            paramGroup.className = 'param-group';
            paramGroup.innerHTML = `
                <h4>Параметр ${param}</h4>
                <div class="param-control">
                    <label>Минимум:</label>
                    <input type="number" class="param-min" data-param="${param}" value="1">
                </div>
                <div class="param-control">
                    <label>Максимум:</label>
                    <input type="number" class="param-max" data-param="${param}" value="10">
                </div>
            `;
            paramsContainer.appendChild(paramGroup);
        });
    }
    
    // Добавление нового шаблона
    document.getElementById('addTemplateBtn').addEventListener('click', function() {
        const name = document.getElementById('templateName').value.trim();
        const question = questionInput.value.trim();
        const answer = answerInput.value.trim();
        
        if (!name || !question || !answer) {
            alert('Заполните все поля');
            return;
        }
        
        // Собираем параметры
        const params = {};
        document.querySelectorAll('.param-group').forEach(group => {
            const param = group.querySelector('.param-min').dataset.param;
            const min = parseInt(group.querySelector('.param-min').value);
            const max = parseInt(group.querySelector('.param-max').value);
            
            if (min >= max) {
                alert(`Для параметра ${param} максимум должен быть больше минимума`);
                return;
            }
            
            params[param] = { min, max };
        });
        
        // Отправляем на сервер
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
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Шаблон успешно добавлен');
                window.location.reload();
            } else {
                alert('Ошибка: ' + (data.error || 'неизвестная ошибка'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при сохранении шаблона');
        });
    });
    
    // Инициализация параметров
    updateParameters();
});