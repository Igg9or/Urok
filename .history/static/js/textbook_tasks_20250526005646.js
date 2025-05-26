document.addEventListener('DOMContentLoaded', function() {
    const textbookId = document.querySelector('.textbook-tasks-container').dataset.textbookId;
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const selectedCount = document.getElementById('selectedCount');
    
    // Инициализация чекбоксов
    function initCheckboxes() {
        const checkboxes = document.querySelectorAll('.template-checkbox');
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateSelection);
        });
        
        updateSelection();
    }
    
    // Обновление состояния кнопок
    function updateSelection() {
        const selected = document.querySelectorAll('.template-checkbox:checked');
        selectedCount.textContent = selected.length;
        deleteSelectedBtn.disabled = selected.length === 0;
    }
    
    // Выбрать все/снять выделение
    selectAllBtn.addEventListener('click', function() {
        const checkboxes = document.querySelectorAll('.template-checkbox');
        const allChecked = checkboxes.length === document.querySelectorAll('.template-checkbox:checked').length;
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = !allChecked;
        });
        
        updateSelection();
    });
    
    // Массовое удаление
    deleteSelectedBtn.addEventListener('click', function() {
        const selectedIds = Array.from(document.querySelectorAll('.template-checkbox:checked'))
            .map(checkbox => checkbox.closest('.template-card').dataset.id);
        
        if (selectedIds.length === 0) return;
        
        if (confirm(`Вы уверены, что хотите удалить ${selectedIds.length} выбранных шаблонов?`)) {
            fetch('/teacher/bulk_delete_templates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    textbook_id: textbookId,
                    template_ids: selectedIds
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('Ошибка: ' + (data.error || 'Не удалось удалить шаблоны'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при удалении');
            });
        }
    });
    
    // Инициализация
    initCheckboxes();
});