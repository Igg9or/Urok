import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        if not all(key in template for key in ['question_template', 'answer_template', 'parameters']):
            return None

        # Генерация параметров (всегда словарь, даже если пустой)
        params = {}
        if template.get('parameters'):
            params = MathEngine.generate_parameters(template['parameters'])
        # Если в шаблоне есть formulas — вычислить их и добавить к params
        derived = template.get('derived_parameters', {})
        for var, expr in derived.items():
            try:
                local_vars = dict(params)
                params[var] = eval(expr, {}, local_vars)
            except Exception as e:
                print(f"[derived_parameters] Ошибка вычисления {var} = {expr}: {e}")
                params[var] = None

        # Формируем вопрос (подставляем параметры, если есть)
        question = template['question_template']
        if params:
            for param, value in params.items():
                question = re.sub(rf"\{{{param}\}}", str(value), question)

        # Главный блок: универсальная подстановка для ответа
        def eval_expr(match):
            expr = match.group(1)
            try:
                # Разрешённые функции для использования в шаблоне
                safe_funcs = {
                    'round': round,
                    'abs': abs,
                    'min': min,
                    'max': max
                }
                # Добавляем параметры в locals
                local_vars = dict(params)
                # Если expr — имя параметра (строка или число), просто возвращаем как есть
                if expr in local_vars:
                    val = local_vars[expr]
                    if val is None:
                        return "Ошибка: параметр не определён"
                    return str(val)
                # Если хотя бы один арифм. оператор или round — вычисляем
                if any(op in expr for op in '+-*/') or 'round' in expr or 'abs' in expr or 'min' in expr or 'max' in expr:
                    return str(eval(expr, safe_funcs, local_vars))
                return str(eval(expr, safe_funcs, local_vars))
            except Exception as e:
                print(f"Ошибка вычисления '{expr}': {e}")
                return "Ошибка генерации"

        answer_template = template['answer_template']
        answer = re.sub(r"\{([^{}]+)\}", eval_expr, answer_template)

        return {
            'question': question,
            'correct_answer': answer,
            'params': params,
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
