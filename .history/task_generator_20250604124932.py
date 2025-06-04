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
                    return str(local_vars[expr])
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
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))
