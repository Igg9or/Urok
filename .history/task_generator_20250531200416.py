import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template: dict) -> dict:
        """Генерирует вариант задания на основе шаблона"""
        # Генерация параметров
        params = MathEngine.generate_parameters(template['parameters'])
        
        # Дополнительная проверка условий (на случай, если MathEngine не справился)
        conditions = template.get('conditions')
        if conditions:
            try:
                if not eval(conditions, {}, params):
                    raise ValueError("Сгенерированные параметры не удовлетворяют условиям")
            except Exception as e:
                print(f"Ошибка проверки условий: {e}")
                # Можно попробовать сгенерировать заново или вернуть ошибку
        
        # Формирование вопроса
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))
        
        # Вычисление ответа
        answer = MathEngine.evaluate_expression(template['answer_template'], params)
        
        return {
            'question': question,
            'correct_answer': answer,
            'params': params,
            'template_id': template.get('id')
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))