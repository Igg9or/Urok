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
        conditions = template.get('conditions')
        
        if conditions:
            # conditions могут быть типа "dm = A // 10; cm = A % 10"
            for expr in conditions.split(';'):
                expr = expr.strip()
                if not expr:
                    continue
                # Парсим: "dm = A // 10"
                m = re.match(r'(\w+)\s*=\s*(.+)', expr)
                if m:
                    var, code = m.groups()
                    # Подставляем уже сгенерированные params в выражение
                    # Заменяем имена переменных на значения
                    expr_for_eval = code
                    for p_name, p_val in params.items():
                        expr_for_eval = re.sub(rf'\b{p_name}\b', str(p_val), expr_for_eval)
                    try:
                        params[var] = eval(expr_for_eval)
                    except Exception as e:
                        print(f"Ошибка вычисления условия '{expr}': {e}")
        # Замена в вопросе
        question = template['question_template']
        answer_template = template['answer_template']

        # Извлекаем все параметры из вопроса и ответа
        question_params = set(re.findall(r'\{([A-Za-z]+)\}', question))
        answer_params = set(re.findall(r'\{([A-Za-z]+)\}', answer_template))
        all_params = question_params.union(answer_params)

        # Генерируем значения для всех параметров
        for param in all_params:
            if param not in params:
                # Если параметр не указан в конфигурации, генерируем случайное значение
                params[param] = random.randint(1, 10)

        # Заменяем параметры в вопросе
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))

        # Вычисление ответа
        try:
            answer = str(eval(answer_template.format(**params)))
        except Exception as e:
            print(f"Ошибка вычисления ответа: {e}")
            answer = "Неверная формула ответа"

        return {
            'question': question,
            'correct_answer': answer,
            'params': params,
            'template_id': template.get('id'),
            'answer_type': template.get('answer_type', 'numeric')
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))