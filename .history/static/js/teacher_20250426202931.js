document.addEventListener('DOMContentLoaded', function() {
    // Выбор класса
    const gradeButtons = document.querySelectorAll('.btn-grade');
    const letterButtons = document.querySelector('.letter-buttons');
    const classActions = document.getElementById('classActions');
    
    let selectedGrade = null;
    
    gradeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            gradeButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedGrade = this.dataset.grade;
            letterButtons.classList.remove('hidden');
        });
    });
    
    // Выбор буквы класса
    document.querySelectorAll('.btn-letter').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.btn-letter').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            classActions.classList.remove('hidden');
        });
    });
    
    // Модальное окно создания урока
    const modal = document.getElementById('lessonModal');
    const createBtn = document.getElementById('createNewLesson');
    const closeBtn = document.querySelector('.close');
    
    createBtn.addEventListener('click', function() {
        modal.classList.remove('hidden');
    });
    
    closeBtn.addEventListener('click', function() {
        modal.classList.add('hidden');
    });
    
    // Добавление параметров
    const addParamBtn = document.getElementById('addParam');
    const paramControls = document.getElementById('paramControls');
    
    // Открытие модального окна
document.getElementById('createNewLesson').addEventListener('click', function() {
    document.getElementById('lessonModal').classList.remove('hidden');
});

// Закрытие через крестик
document.querySelector('.close').addEventListener('click', function() {
    document.getElementById('lessonModal').classList.add('hidden');
});

// Закрытие при клике вне окна
window.addEventListener('click', function(event) {
    const modal = document.getElementById('lessonModal');
    if (event.target === modal) {
        modal.classList.add('hidden');
    }
});

    addParamBtn.addEventListener('click', function() {
        const paramName = prompt('Введите имя параметра (одна буква):', 'A');
        if (paramName && /^[A-Za-z]$/.test(paramName)) {
            const paramControl = document.createElement('div');
            paramControl.className = 'param-control';
            paramControl.innerHTML = `
                <span>${paramName}:</span>
                <input type="number" placeholder="Минимум" class="param-min">
                <input type="number" placeholder="Максимум" class="param-max">
                <button class="btn btn-small remove-param">×</button>
            `;
            paramControls.appendChild(paramControl);
            
            paramControl.querySelector('.remove-param').addEventListener('click', function() {
                paramControls.removeChild(paramControl);
            });
        }
    });
    
    // Сохранение урока
    const saveLessonBtn = document.getElementById('saveLesson');
    
    saveLessonBtn.addEventListener('click', function() {
        const template = document.getElementById('taskTemplate').value;
        
        // Автоматически находим параметры в шаблоне
        const paramsInTemplate = [...new Set(template.match(/\{([A-Za-z])\}/g))];
        const params = {};
        
        paramsInTemplate.forEach(param => {
            const paramName = param.replace(/\{|\}/g, '');
            const minInput = document.querySelector(`.param-control input[data-param="${paramName}"][data-type="min"]`);
            const maxInput = document.querySelector(`.param-control input[data-param="${paramName}"][data-type="max"]`);
            
            if (minInput && maxInput) {
                params[paramName] = {
                    min: parseInt(minInput.value),
                    max: parseInt(maxInput.value)
                };
            }
        });
        
        // Отправляем на сервер
        fetch('/teacher/create_lesson', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                grade: selectedGrade,
                template: template,
                params: params
            })
        })
        .then(response => response.json())
        .then(data => {
            alert('Урок успешно создан!');
            modal.classList.add('hidden');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при создании урока');
        });
    });
});