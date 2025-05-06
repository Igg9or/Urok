document.addEventListener('DOMContentLoaded', function() {
    const lessonId = window.location.pathname.split('/').pop();
    const refreshBtn = document.getElementById('refreshResults');
    const endLessonBtn = document.getElementById('endLesson');
    
    // Функция загрузки результатов
    function loadResults() {
        fetch(`/teacher/get_lesson_results/${lessonId}`)
            .then(response => response.json())
            .then(data => {
                data.results.forEach(student => {
                    // Обновляем прогресс для каждого ученика
                    const correctCount = student.tasks.filter(t => t.is_correct).length;
                    const totalTasks = student.tasks.length;
                    const percentage = totalTasks > 0 ? Math.round((correctCount / totalTasks) * 100) : 0;
                    
                    // Находим строку ученика в таблице
                    const studentRow = document.querySelector(`tr[data-student-id="${student.user_id}"]`) || 
                                     document.querySelector(`tr:has(td:first-child:contains("${student.full_name}"))`);
                    
                    if (studentRow) {
                        // Обновляем результаты по заданиям
                        student.tasks.forEach((task, index) => {
                            const taskCell = studentRow.querySelector(`td[data-task-id="${task.task_id}"]`);
                            if (taskCell) {
                                if (task.answered) {
                                    taskCell.innerHTML = task.is_correct ? 
                                        '<span class="correct">✓</span>' : 
                                        '<span class="incorrect">✗</span>';
                                }
                            }
                        });
                        
                        // Обновляем прогресс
                        const progressBar = studentRow.querySelector('.progress-bar');
                        const progressText = studentRow.querySelector('.progress-container span');
                        if (progressBar && progressText) {
                            progressBar.style.width = `${percentage}%`;
                            progressText.textContent = `${percentage}%`;
                        }
                    }
                });
            });
    }
    
    // Автоматическое обновление каждые 5 секунд
    loadResults();
    const intervalId = setInterval(loadResults, 5000);
    
    // Ручное обновление
    refreshBtn.addEventListener('click', loadResults);
    
    // Завершение урока
    endLessonBtn.addEventListener('click', function() {
        if (confirm('Вы уверены, что хотите завершить урок? После этого ученики не смогут отправлять ответы.')) {
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