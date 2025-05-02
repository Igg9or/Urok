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

    // 6. Сохранение урока (новый вариант)
    saveLessonBtn.addEventListener('click', function() {
        const title = document.getElementById('lessonTitle').value.trim();
        const date = document.getElementById('lessonDate').value;
        
        if (!title) {
            alert('Введите название урока');
            return;
        }
    
        fetch('/teacher/create_lesson', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                grade: `${selectedGrade}${selectedLetter}`,
                title: title,
                date: date
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сервера');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.lesson_id) {
                // Перенаправляем на страницу редактирования
                window.location.href = `/teacher/edit_lesson/${data.lesson_id}`;
            } else {
                throw new Error(data.error || 'Неизвестная ошибка');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Ошибка создания урока: ${error.message}`);
        });
    });

    // Функция для загрузки уроков класса
    function loadLessons(grade, letter) {
        fetch(`/teacher/get_lessons?grade=${grade}${letter}`)
            .then(response => response.json())
            .then(data => {
                const container = document.querySelector('.lessons-container');
                container.innerHTML = '';
                
                if (data.lessons.length === 0) {
                    container.innerHTML = '<p>Нет созданных уроков</p>';
                    return;
                }
                
                data.lessons.forEach(lesson => {
                    const lessonElement = document.createElement('div');
                    lessonElement.className = 'lesson-card';
                    lessonElement.innerHTML = `
                        <div class="lesson-icon">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2L1 12h3v9h6v-6h4v6h6v-9h3L12 2zm0 2.8L18 10v9h-2v-6H8v6H6v-9l6-7.2z"/>
                            </svg>
                        </div>
                        <div class="lesson-info">
                            <h4>${lesson.title}</h4>
                            <p>${lesson.date}</p>
                        </div>
                        <div class="lesson-actions">
                            <a href="/teacher/conduct_lesson/${lesson.id}" class="btn btn-small">Войти в урок</a>
                            <a href="/teacher/edit_lesson/${lesson.id}" class="btn btn-small btn-secondary">Редактировать</a>
                        </div>
                    `;
                    container.appendChild(lessonElement);
                });
                
                document.querySelector('.lessons-list').classList.remove('hidden');
            });
    }

    // Вызываем загрузку уроков при выборе класса и буквы
    document.querySelectorAll('.btn-letter').forEach(btn => {
        btn.addEventListener('click', function() {
            // ... существующий код ...
            loadLessons(selectedGrade, selectedLetter);
        });
    });
});