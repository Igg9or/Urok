# utils/task_generator.py
import random
import re
import json
from typing import Dict, Any, List, Tuple

class TaskGenerator:
    @staticmethod
    def generate_task_variant(question: str, answer_template: str, parameters: dict) -> dict:
    params = {}
    
    # Генерация параметров
    for param, config in parameters.items():
        if config.get('type', 'int') == 'float':
            params[param] = round(random.uniform(config['min'], config['max']), 2)
        else:
            params[param] = random.randint(config['min'], config['max'])
    
    # Подстановка в вопрос
    generated_question = question
    for p, v in params.items():
        generated_question = generated_question.replace(f'{{{p}}}', str(v))
    
    # Вычисление ответа
    try:
        # Подготовка выражения
        expr = answer_template
        for p, v in params.items():
            expr = expr.replace(f'{{{p}}}', str(v))
        
        # Замена математических символов
        expr = expr.replace('×', '*').replace('÷', '/').replace('^', '**')
        
        # Безопасное вычисление
        allowed_chars = {'0','1','2','3','4','5','6','7','8','9','+','-','*','/','.',' ','(',')'}
        if all(c in allowed_chars for c in expr):
            result = eval(expr)
            computed_answer = str(round(result, 2) if isinstance(result, float) else result)
        else:
            computed_answer = "Недопустимые символы в выражении"
    except Exception as e:
        computed_answer = f"Ошибка вычисления: {str(e)}"
    
    return {
        'question': generated_question,
        'correct_answer': computed_answer,
        'params': params
    }

    @staticmethod
    def extract_parameters(template: str) -> List[str]:
        """Извлекает список параметров из шаблона"""
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template)))