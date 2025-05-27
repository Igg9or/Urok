# utils/task_generator.py
import random
import re
import json
from typing import Dict, Any, List, Tuple

class TaskGenerator:
    @staticmethod
    def generate_task_variant(question: str, answer_template: str, parameters: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """
        Генерирует вариант задания с подставленными параметрами
        """
        params = {}
        
        # Генерация значений параметров с учетом ограничений
        for param, config in parameters.items():
            valid = False
            value = None
            
            # Пытаемся сгенерировать валидное значение (до 100 попыток)
            for _ in range(100):
                if config.get('type', 'int') == 'float':
                    value = random.uniform(config['min'], config['max'])
                else:
                    value = random.randint(config['min'], config['max'])
                
                valid = True
                
                # Проверяем дополнительные ограничения
                if 'constraints' in config:
                    for constraint in config['constraints']:
                        if constraint['type'] == 'multiple_of' and value % constraint['value'] != 0:
                            valid = False
                        elif constraint['type'] == 'greater_than':
                            compare_to = params.get(constraint.get('param'), constraint['value'])
                            if value <= compare_to:
                                valid = False
                
                if valid:
                    break
            
            params[param] = value if valid else config['min']  # fallback
        
        # Подставляем параметры в вопрос
        generated_question = question
        for param, value in params.items():
            generated_question = generated_question.replace(f'{{{param}}}', str(value))
        
        # Вычисляем ответ
        try:
            computed_answer = str(eval(answer_template.format(**params)))
        except:
            computed_answer = "Ошибка в формуле ответа"
        
        return {
            'question': generated_question,
            'correct_answer': computed_answer,
            'params': params
        }

    @staticmethod
    def extract_parameters(template: str) -> List[str]:
        """Извлекает список параметров из шаблона"""
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template)))