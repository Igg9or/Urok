import random
import re
import json
from math import gcd
from fractions import Fraction
import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations
from math_engine import MathEngine

class TaskGenerator:
    @staticmethod
def generate_task_variant(template):
    if not template:
        return None

    try:
        # Генерация параметров с защитой от ошибок
        params = MathEngine.generate_parameters(template.get('parameters', {}))
        
        # Обработка derived_parameters
        derived = template.get('derived_parameters', {})
        for var, expr in derived.items():
            try:
                params[var] = eval(expr, {}, params)
            except:
                params[var] = None

        # Генерация вопроса
        question = template.get('question_template', '')
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))

        # Генерация ответа
        answer = TaskGenerator.generate_answer(template, params)

        return {
            'question': question if question else "Не удалось сгенерировать вопрос",
            'correct_answer': answer if answer else "Не удалось сгенерировать ответ",
            'params': params,
            'template_id': template.get('id'),
            'answer_type': template.get('answer_type', 'numeric')
        }

    except Exception as e:
        print(f"Task generation error: {str(e)}")
        return {
            'question': "Ошибка генерации задания",
            'correct_answer': "Ошибка генерации ответа",
            'params': {},
            'template_id': template.get('id')
        }

    @staticmethod
    def generate_answer(template, params):
        """Генерация ответа с учетом типа"""
        answer_type = template.get('answer_type', 'numeric')
        raw_answer = template['answer_template'].format(**params)
        
        if answer_type == 'fraction':
            try:
                # Вычисление дроби с сокращением
                parts = raw_answer.split('/')
                if len(parts) == 2:
                    num, den = int(parts[0]), int(parts[1])
                    gcd_val = gcd(num, den)
                    return f"{num//gcd_val}/{den//gcd_val}"
            except:
                pass
            return raw_answer
        
        elif answer_type == 'expression':
            try:
                # Упрощение выражения
                expr = parse_expr(raw_answer, transformations=standard_transformations)
                return str(sympy.simplify(expr))
            except:
                return raw_answer
        
        return raw_answer  # numeric по умолчанию

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))
