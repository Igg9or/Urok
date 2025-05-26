import json
import random
import sqlite3
from typing import Dict, Any

class MakarichevTaskLoader:
    def __init__(self, db_path: str = 'database.db'):
        self.db_path = db_path
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Загружает шаблоны для учебника Макарычева"""
        with open('makarichev_templates.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {t['id']: t for t in data['templates']}
    
    def _generate_param(self, param: str, constraints: Dict[str, Any], existing: Dict[str, int]) -> int:
        """Генерирует параметр с учётом ограничений"""
        # Если параметр вычисляется по выражению
        if 'expression' in constraints:
            X = random.randint(constraints['X']['min'], constraints['X']['max'])
            return eval(constraints['expression'], {'X': X}, existing)
        
        # Если есть конкретные значения
        if 'values' in constraints:
            return random.choice(constraints['values'])
        
        # Если должен делиться на другой параметр
        if 'divisible_by' in constraints:
            divisor = existing[constraints['divisible_by']]
            min_val = constraints.get('min', 1)
            max_val = constraints.get('max', 100)
            
            # Подбираем кратное число в диапазоне
            start = (min_val // divisor) * divisor
            if start < min_val:
                start += divisor
            end = (max_val // divisor) * divisor
            return random.randrange(start, end + 1, divisor)
        
        # Обычный случай
        return random.randint(
            constraints.get('min', 1),
            constraints.get('max', 100)
        )
    
    def generate_task(self, template_id: str) -> str:
        """Генерирует конкретное задание"""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Шаблон {template_id} не найден")
        
        for _ in range(100):  # Максимум 100 попыток
            params = {}
            try:
                # Генерируем параметры в правильном порядке
                for param in template['constraints']:
                    params[param] = self._generate_param(param, template['constraints'][param], params)
                
                # Проверяем дополнительные правила
                if all(eval(rule, {}, params) for rule in template.get('rules', [])):
                    return template['template'].format(**params)
            
            except (ZeroDivisionError, KeyError):
                continue
        
        raise RuntimeError(f"Не удалось сгенерировать задание {template_id}")
    
    def add_to_textbook(self, num_tasks: int = 10):
        """Добавляет задания в учебник Макарычева"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем существование учебника
        cursor.execute("SELECT id FROM textbooks WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO textbooks (id, title, description, grade)
                VALUES (1, 'Макарычев', 'Алгебра для 5 класса', 5)
            ''')
        
        # Добавляем задания
        for _ in range(num_tasks):
            template_id = random.choice(list(self.templates.keys()))
            question = self.generate_task(template_id)
            template = self.templates[template_id]
            
            cursor.execute('''
                INSERT INTO task_templates 
                (textbook_id, name, question_template, answer_template, parameters, difficulty) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                1,  # ID учебника Макарычева
                template['name'],
                question,
                "",  # Ответ можно вычислить отдельно
                json.dumps(template['constraints']),
                template['difficulty']
            ))
        
        conn.commit()
        conn.close()
        print(f"Успешно добавлено {num_tasks} заданий в учебник Макарычева")

# Пример использования
if __name__ == "__main__":
    loader = MakarichevTaskLoader()
    
    # Сгенерировать пример задания
    print("Пример задания:", loader.generate_task("makarichev_subtract_divide"))
    
    # Добавить 15 заданий в учебник
    loader.add_to_textbook(num_tasks=15)