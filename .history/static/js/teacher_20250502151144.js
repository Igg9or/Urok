document.addEventListener('DOMContentLoaded', function() {
    // Элементы интерфейса
    const gradeButtons = document.querySelectorAll('.btn-grade');
    const letterButtons = document.querySelector('.letter-buttons');
    const createBtn = document.getElementById('createNewLesson');
    const modal = document.getElementById('lessonModal');
    const closeBtn = document.querySelector('.close');
    const addParamBtn = document.getElementById('addParam');
    const paramControls = document.getElementById('paramControls');
    const saveLessonBtn = document.getElementById('saveLesson');
    
    let selectedGrade = null;
    let selectedLetter = null;

    // 1. Выбор класса (5-11)
    gradeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Снимаем выделение с других кнопок
            gradeButtons.forEach(b => b.classList.remove('active'));
            // Выделяем текущую
            this.classList.add('active');
            
            selectedGrade = this.dataset.grade;
            letterButtons.classList.remove('hidden');
            createBtn.classList.add('hidden'); // Скрываем кнопку, пока не выберут букву
        });
    });

    // 2. Выбор буквы класса (А-Д)
    document.querySelectorAll('.btn-letter').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.btn-letter').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            selectedLetter = this.dataset.letter;
            createBtn.classList.remove('hidden');
        });
    });

    // 3. Открытие модального окна
    createBtn.addEventListener('click', function() {
        modal.classList.remove('hidden');
    });

    // 4. Закрытие модального окна
    function closeModal() {
        modal.classList.add('hidden');
    }
    
    closeBtn.addEventListener('click', closeModal);
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // 5. Добавление параметров
    addParamBtn.addEventListener('click', function() {
        const paramName = prompt('Введите имя параметра (одна буква, например A):');
        if (paramName && /^[A-Za-zА-Яа-я]$/.test(paramName)) {
            const paramRow = document.createElement('div');
            paramRow.className = 'param-row';
            paramRow.innerHTML = `
                <span>${paramName}:</span>
                <input type="number" placeholder="Минимум" data-param="${paramName}" data-type="min">
                <input type="number" placeholder="Максимум" data-param="${paramName}" data-type="max">
                <button class="btn-remove-param">×</button>
            `;
            paramControls.appendChild(paramRow);
            
            // Удаление параметра
            paramRow.querySelector('.btn-remove-param').addEventListener('click', function() {
                paramControls.removeChild(paramRow);
            });
        } else if (paramName) {
            alert('Имя параметра должно быть одной буквой!');
        }
    });

    ие урока
    saveLe// 6. СохраненssonBtn.addEventListener('click', function() {
        const template = document.getElementById('taskTemplate').value;
        
        // Автоматически находим параметры в шаблоне
        const params = {};
        const paramRegex = /\{([A-Za-zА-Яа-я])\}/g;
        let match;
        
        while ((match = paramRegex.exec(template)) !== null) {
            const paramName = match[1];
            const minInput = document.querySelector(`input[data-param="${paramName}"][data-type="min"]`);
            const maxInput = document.querySelector(`input[data-param="${paramName}"][data-type="max"]`);
            
            if (minInput && maxInput) {
                params[paramName] = {
                    min: parseInt(minInput.value) || 0,
                    max: parseInt(maxInput.value) || 10
                };
            } else {
                alert(`Для параметра ${paramName} не заданы диапазоны!`);
                return;
            }
        }
        
        if (Object.keys(params).length === 0) {
            alert('Добавьте хотя бы один параметр в шаблон!');
            return;
        }

        // Отправка данных на сервер
        fetch('/teacher/create_lesson', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                grade: `${selectedGrade}${selectedLetter}`,
                template: template,
                params: params
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Урок успешно создан!');
                closeModal();
                // Очищаем форму
                document.getElementById('taskTemplate').value = '';
                paramControls.innerHTML = '';
            } else {
                alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка соединения с сервером');
        });
    });
});