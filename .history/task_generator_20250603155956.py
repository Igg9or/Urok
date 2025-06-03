import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        # Генерация базовых параметров (A, B, C...)
        params = MathEngine.generate_parameters(template['parameters'])

        # Вычисляем дополнительные параметры (dm, cm) из conditions
        if 'conditions' in template and template['conditions']:
            try:
                # Создаём локальный словарь для exec
                local_vars = {}
                exec(template['conditions'], {}, local_vars)
                
                # Добавляем вычисленные переменные в params
                for var_name, var_value in local_vars.items():
                    params[var_name] = var_value
            except Exception as e:
                print(f"Ошибка в условиях: {e}")

        # Формируем вопрос
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))

        # Вычисляем ответ (учитываем строковые шаблоны)
        answer_template = template['answer_template']
        
        if isinstance(answer_template, str) and "{" in answer_template:
            # Если ответ — строка с подстановками (например, "{dm} дм {cm} см")
            computed_answer = answer_template.format(**params)
        else:
            # Если ответ — математическое выражение (например, "A + B")
            computed_answer = MathEngine.evaluate_expression(answer_template, params)

        return {
            'question': question,
            'correct_answer': computed_answer,
            'params': params,
            'template_id': template.get('id')
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))