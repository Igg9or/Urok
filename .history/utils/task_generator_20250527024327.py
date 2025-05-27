# utils/task_generator.py
import random
import re
import json
from typing import Dict, Any, List, Tuple

class TaskGenerator:
    @staticmethod
def generate_task_variant(question: str, answer_template: str, parameters: dict) -> dict:
    # 1. Генерируем значения параметров
    params = {k: random.randint(v['min'], v['max']) for k, v in parameters.items()}
    
    # 2. Формируем вопрос с подставленными значениями
    generated_question = question
    for param, value in params.items():
        generated_question = generated_question.replace(f'{{{param}}}', str(value))
    
    # 3. Вычисляем ответ
    try:
        # Создаем локальные переменные для eval
        locals().update(params)
        
        # Вычисляем ответ (убираем фигурные скобки из шаблона)
        expr = answer_template.replace('{', '').replace('}', '')
        computed_answer = str(eval(expr, {}, locals()))
    except Exception as e:
        computed_answer = f"Error: {str(e)}"
    
    return {
        'question': generated_question,
        'correct_answer': computed_answer,
        'params': params
    }

    @staticmethod
    def extract_parameters(template: str) -> List[str]:
        """Извлекает список параметров из шаблона"""
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template)))