document.addEventListener('DOMContentLoaded', function() {
    const tasksContainer = document.getElementById('tasksContainer');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const saveLessonBtn = document.getElementById('saveLessonBtn');
    const lessonId = window.location.pathname.split('/').pop();

    // Добавление нового задания
    addTaskBtn.addEventListener('click', function() {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.innerHTML = `
            <textarea class="task-question" placeholder="Введите вопрос"></textarea>
            <textarea class="task-answer" placeholder="Введите ответ"></textarea>
            <button class="btn btn-danger btn-remove-task">Удалить</button>
        `;
        tasksContainer.appendChild(taskCard);
    });

    // Удаление задания
    tasksContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-