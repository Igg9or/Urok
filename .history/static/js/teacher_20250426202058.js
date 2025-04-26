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
        const answerLogic = document.getElementById('answerLogic').value;
        
        // Собираем параметры
        const params = {};
        document.querySelectorAll('.param-control').forEach(control => {
            const name = control.querySelector('span').textContent.replace(':', '');
            const min = control.querySelector('.param-min').value;
            const max = control.querySelector('.param-max').value;
            
            params[name] = { min: parseInt(min), max: parseInt(max) };
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
                params: params,
                answer_logic: answerLogic
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