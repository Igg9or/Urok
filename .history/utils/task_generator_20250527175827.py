# utils/task_generator.py
import random
import re
import json
from typing import Dict, Any, List, Tuple
from math_engine import MathEngine

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template: dict) -> dict:
        """
        Генерирует вариант задания на основе шаблона
        """
        # Генерация параметров
        params = MathEngine.generate_parameters(template['parameters'])
        
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
    def extract_parameters(template: str) -> List[str]:
        """Извлекает список параметров из шаблона"""
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template)))

    @staticmethod
    def validate_template(template: dict) -> bool:
        """Проверяет корректность шаблона"""
        required_fields = ['question_template', 'answer_template', 'parameters']
        if not all(field in template for field in required_fields):
            return False
        
        try:
            # Проверка генерации хотя бы одного варианта
            variant = TaskGenerator.generate_task_variant(template)
            if variant['correct_answer'] is None:
                return False
            return True
        except:
            return False