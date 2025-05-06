document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    const refreshBtn = document.getElementById('refreshResults');
    const endLessonBtn = document.getElementById('endLesson');
    
    // Загрузка результатов
    function loadResults() {
        fetch(`/teacher/get_lesson_results/${lessonId}`)
            .then(response => response.json())
            .then(data => {
                const tableBody = document.getElementById('studentsResults');
                tableBody.innerHTML = '';
                
                data.results.forEach(student => {
                    const row = document.createElement('tr');
                    
                    // Имя ученика
                    const nameCell = document.createElement('td');
                    nameCell.textContent = student.full_name;
                    row.appendChild(nameCell);
                    
                    // Результаты по заданиям
                    let correctCount = 0;
                    
                    student.tasks.forEach(task => {
                        const taskCell = document.createElement('td');
                        
                        if (task.answered) {
                            taskCell.innerHTML = task.is_correct ? 
                                '<span class="correct">✓</span>' : 
                                '<span class="incorrect">✗</span>';
                            if (task.is_correct) correctCount++;
                        } else {
                            taskCell.innerHTML = '<span class="pending">—</span>';
                        }
                        
                        row.appendChild(taskCell);
                    });
                    
                    // Прогресс
                    const progressCell = document.createElement('td');
                    const percentage = student.tasks.length > 0 ? 
                        Math.round((correctCount / student.tasks.length) * 100) : 0;
                    progressCell.innerHTML = `
                        <div class="progress-container">
                            <div class="progress-bar" style="width: ${percentage}%"></div>
                            <span>${percentage}%</span>
                        </div>
                    `;
                    row.appendChild(progressCell);
                    
                    tableBody.appendChild(row);
                });
            });
    }
    
    // Обновление результатов каждые 5 секунд
    loadResults();
    const intervalId = setInterval(loadResults, 5000);
    
    // Ручное обновление
    refreshBtn.addEventListener('click', loadResults);
    
    // Завершение урока
    endLessonBtn.addEventListener('click', function() {
        if (confirm('Завершить урок? После этого ученики не смогут отправлять ответы.')) {
            fetch(`/teacher/end_lesson/${lessonId}`, {
                method: 'POST'
            }).then(response => {
                if (response.ok) {
                    window.location.href = '/teacher/dashboard';
                }
            });
        }
    });
    
    // Очистка интервала при закрытии страницы
    window.addEventListener('beforeunload', function() {
        clearInterval(intervalId);
    });
});