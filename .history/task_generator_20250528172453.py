import re
from math_engine import MathEngine

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        # Проверка обязательных полей
        required_fields = ['question_template', 'answer_template', 'parameters']
        if not all(field in template for field in required_fields):
            return None

        # Генерация параметров с учетом условий
        params = MathEngine.generate_parameters(template['parameters'])
        if not params:
            return None

        # Извлекаем ВСЕ параметры из вопроса и ответа
        question_params = set(re.findall(r'\{([A-Za-z]+)\}', template['question_template']))
        answer_params = set(re.findall(r'\{([A-Za-z]+)\}', template['answer_template']))
        all_params = question_params.union(answer_params)

        # Проверяем, что все параметры есть в сгенерированных значениях
        for param in all_params:
            if param not in params:
                # Если параметра нет - генерируем случайное значение
                params[param] = random.randint(1, 10)

        # Заменяем параметры в вопросе
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))

        # Вычисляем ответ
        try:
            answer_expr = template['answer_template']
            # Двойная замена на случай вложенных выражений
            for param, value in params.items():
                answer_expr = answer_expr.replace(f'{{{param}}}', str(value))
            answer = str(eval(answer_expr))
        except Exception as e:
            print(f"Ошибка вычисления ответа: {e}")
            answer = "Неверная формула ответа"

        return {
            'question': question,
            'correct_answer': answer,
            'params': params
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))