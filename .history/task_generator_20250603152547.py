import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        # Проверяем наличие всех необходимых полей
        if not all(key in template for key in ['question_template', 'answer_template', 'parameters']):
            return None

        # Генерация параметров
        params = MathEngine.generate_parameters(template['parameters'])
        if not params:
            return None

        # Замена в вопросе
        question = template['question_template']
        answer_template = template['answer_template']
        answer_type = template.get('answer_type', 'numeric')  # default: numeric

        # Извлекаем все параметры из вопроса и ответа
        question_params = set(re.findall(r'\{([A-Za-z]+)\}', question))
        answer_params = set(re.findall(r'\{([A-Za-z]+)\}', answer_template))
        all_params = question_params.union(answer_params)

        # Генерируем значения для всех параметров
        for param in all_params:
            if param not in params:
                params[param] = random.randint(1, 10)

        # Заменяем параметры в вопросе
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))

        # Вычисление/генерация ответа в зависимости от типа
        if answer_type == "numeric":
            try:
                answer = str(eval(answer_template.format(**params)))
            except Exception as e:
                print(f"Ошибка вычисления ответа: {e}")
                answer = "Неверная формула ответа"
        elif answer_type == "expression":
            # Подставляем значения, но сохраняем переменные (например, "2x+3x")
            try:
                # Формируем строку-выражение
                answer_str = answer_template.format(**params)
                # Симплификация (по желанию): можно упростить выражение
                answer = str(sympy.simplify(answer_str))
            except Exception as e:
                print(f"Ошибка символьного ответа: {e}")
                answer = "Ошибка в выражении"
        elif answer_type == "text":
            # Просто подставляем параметры, не вычисляя
            try:
                answer = answer_template.format(**params)
            except Exception as e:
                print(f"Ошибка текстового ответа: {e}")
                answer = "Ошибка в ответе"
        else:
            # fallback — старый способ
            try:
                answer = str(eval(answer_template.format(**params)))
            except Exception as e:
                print(f"Ошибка вычисления ответа (fallback): {e}")
                answer = "Неверная формула ответа"

        return {
            'question': question,
            'correct_answer': answer,
            'params': params,
            'template_id': template.get('id')
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))