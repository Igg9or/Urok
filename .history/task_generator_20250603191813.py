import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        if not all(key in template for key in ['question_template', 'answer_template', 'parameters']):
            return None

        params = MathEngine.generate_parameters(template['parameters'])
        if not params:
            return None

        # Формируем вопрос (просто заменяем параметры)
        question = template['question_template']
        for param, value in params.items():
            question = re.sub(rf"\{{{param}\}}", str(value), question)

        # Главный ХАК: вычисляем все {...} как python-выражения!
        def eval_expr(match):
            expr = match.group(1)
            try:
                return str(eval(expr, {}, params))
            except Exception as e:
                print(f"Ошибка вычисления '{expr}': {e}")
                return "?"

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
