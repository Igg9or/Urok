document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    const refreshBtn = document.getElementById('refreshResults');
    const endLessonBtn = document.getElementById('endLesson');
    let studentIds = [];
    
    // Получаем ID всех учеников
    document.querySelectorAll('#studentsResults tr').forEach(row => {
        studentIds.push(row.dataset.studentId || row.cells[0].textContent.trim());
    });
    
    // Функция обновления результатов
    async function updateResults() {
        try {
            const response = await fetch(`/teacher/get_lesson_results/${lessonId}`);
            const data = await response.json();
            
            if (data.results) {
                data.results.forEach(studentData => {
                    updateStudentRow(studentData);
                });
            }
        } catch (error) {
            console.error('Error updating results:', error);
        }
    }
    
    // Обновляем строку конкретного ученика
    function updateStudentRow(studentData) {
        const row = document.querySelector(`tr[data-student-id="${studentData.user_id}"]`);
        if (!row) return;
        
        // Обновляем задания
        studentData.tasks.forEach((task, index) => {
            const taskCell = row.cells[index + 1]; // +1 потому что первая ячейка - имя
            if (taskCell) {
                taskCell.innerHTML = task.answered 
                    ? (task.is_correct 
                        ? '<span class="correct">✓</span>' 
                        : '<span class="incorrect">✗</span>')
                    : '<span class="pending">—</span>';
            }
        });
        
        // Обновляем прогресс
        const progressBar = row.querySelector('.progress-bar');
        const progressText = row.querySelector('.progress-container span');
        if (progressBar && progressText) {
            progressBar.style.width = `${studentData.progress}%`;
            progressText.textContent = `${studentData.progress}%`;
        }
    }
    
    // Первоначальная загрузка
    updateResults();
    
    // Автоматическое обновление каждые 3 секунды
    const intervalId = setInterval(updateResults, 3000);
    
    // Ручное обновление
    refreshBtn.addEventListener('click', updateResults);
    
    // Завершение урока
    endLessonBtn.addEventListener('click', function() {
        if (confirm('Завершить урок? Ученики больше не смогут отвечать.')) {
            fetch(`/teacher/end_lesson/${lessonId}`, {
                method: 'POST'
            }).then(response => {
                if (response.ok) {
                    clearInterval(intervalId);
                    window.location.href = '/teacher/dashboard';
                }
            });
        }
    });
    
    // Очистка при закрытии страницы
    window.addEventListener('beforeunload', () => clearInterval(intervalId));
});