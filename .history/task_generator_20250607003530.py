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
    if not template or not isinstance(template, dict):
        return {
            'question': 'Ошибка: некорректный шаблон',
            'correct_answer': 'Ошибка генерации',
            'params': {}
        }

    # Инициализация параметров с защитой от None
    params = {}
    try:
        raw_params = template.get('parameters', {})
        if isinstance(raw_params, str):
            params = json.loads(raw_params) if raw_params else {}
        elif isinstance(raw_params, dict):
            params = raw_params
        else:
            params = {}
    except:
        params = {}

    # Генерация параметров
    try:
        params = MathEngine.generate_parameters(params) or {}
    except:
        params = {}

    # Обработка derived_parameters
    derived = {}
    try:
        raw_derived = template.get('derived_parameters', {})
        if isinstance(raw_derived, str):
            derived = json.loads(raw_derived) if raw_derived else {}
        elif isinstance(raw_derived, dict):
            derived = raw_derived
    except:
        derived = {}

    for var, expr in derived.items():
        try:
            params[var] = eval(expr, {}, params)
        except:
            params[var] = None

    # Генерация вопроса
    question = template.get('question_template', 'Не указан шаблон вопроса')
    try:
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))
    except:
        question = 'Ошибка подстановки параметров'

    # Генерация ответа
    answer = TaskGenerator.generate_answer(template, params)

    return {
        'question': question,
        'correct_answer': answer,
        'params': params,
        'template_id': template.get('id'),
        'answer_type': template.get('answer_type', 'numeric')
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
