import json
import random
import sqlite3
from typing import Dict, Any

class MakarichevTaskLoader:
    def __init__(self, db_path: str = 'database.db'):
        self.db_path = db_path
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        with open('makarichev_templates.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {t['id']: t for t in data['templates']}
    
    def _generate_param(self, param: str, constraints: Dict[str, Any], existing: Dict[str, int]) -> int:
        try:
            if 'expression' in constraints:
                return eval(constraints['expression'], {'random': random}, existing)
            
            if 'values' in constraints:
                return random.choice(constraints['values'])
            
            if 'divisible_by' in constraints:
                divisor = existing[constraints['divisible_by']]
                min_val = max(constraints.get('min', 1), divisor)
                max_val = constraints.get('max', 100)
                return random.randrange(min_val, max_val + 1, divisor)
            
            return random.randint(
                constraints.get('min', 1),
                constraints.get('max', 100)
        except:
            return 1  # Значение по умолчанию при ошибке
    
    def generate_task(self, template_id: str, max_attempts: int = 50) -> str:
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Шаблон {template_id} не найден")
        
        for _ in range(max_attempts):
            params = {}
            try:
                # Генерация в порядке определения в JSON
                for param in template['constraints']:
                    params[param] = self._generate_param(param, template['constraints'][param], params)
                
                if all(eval(rule, {}, params) for rule in template.get('rules', [])):
                    return template['template'].format(**params)
            except:
                continue
        
        raise RuntimeError(f"Не удалось сгенерировать задание {template_id} после {max_attempts} попыток")
    
    def add_to_textbook(self, num_tasks: int = 10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаём учебник если нужно
        cursor.execute("SELECT 1 FROM textbooks WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO textbooks (id, title, description, grade)
                VALUES (1, 'Макарычев', 'Алгебра для 5 класса', 5)
            ''')
        
        # Добавляем задания
        added = 0
        template_ids = list(self.templates.keys())
        
        while added < num_tasks:
            template_id = random.choice(template_ids)
            try:
                question = self.generate_task(template_id)
                template = self.templates[template_id]
                
                cursor.execute('''
                    INSERT INTO task_templates 
                    (textbook_id, name, question_template, answer_template, parameters, difficulty) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    1,
                    template['name'],
                    question,
                    "",
                    json.dumps(template['constraints']),
                    template['difficulty']
                ))
                added += 1
            except RuntimeError:
                continue
        
        conn.commit()
        conn.close()
        print(f"Успешно добавлено {added} заданий в учебник Макарычева")

if __name__ == "__main__":
    loader = MakarichevTaskLoader()
    
    # Тестируем генерацию каждого типа
    for template_id in loader.templates:
        try:
            print(f"{template_id}:", loader.generate_task(template_id))
        except Exception as e:
            print(f"Ошибка в {template_id}: {str(e)}")
    
    # Добавляем задания в БД
    loader.add_to_textbook(num_tasks=15)