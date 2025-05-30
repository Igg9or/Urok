# task_generator.py
import random
import re
import json
from typing import Dict, Any, List
from math_engine import MathEngine

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template: dict) -> dict:
        """
        Генерирует вариант задания на основе шаблона с поддержкой всех функций
        """
        # Генерация параметров
        params = MathEngine.generate_parameters(template['parameters'])
        
        # Дополнительные вычисления для числовых представлений
        for param, value in params.items():
            if isinstance(value, int):
                # Добавляем текстовое представление
                params[f"{param}_word"] = MathEngine.number_to_words(value)
                # Добавляем форматированное представление
                params[f"{param}_formatted"] = MathEngine.format_number_with_spaces(value)
                # Добавляем читаемое представление
                params[f"{param}_read"] = MathEngine.number_to_words(value)
                
                # Добавляем позиции цифр
                s = str(value)
                for i, d in enumerate(s):
                    params[f"{param}_{d}_pos"] = MathEngine.get_digit_position(value, int(d))
        
        # Формирование вопроса
        question = template['question_template']
        for param, value in params.items():
            if f'{{{param}}}' in question:
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
        return list(set(re.findall(r'\{([A-Za-z0-9_]+)\}', template)))

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
        except Exception as e:
            print(f"Template validation error: {e}")
            return False