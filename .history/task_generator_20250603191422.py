import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        if not all(key in template for key in ['question_template', 'answer_template', 'parameters']):
            return None

        # 1. Генерируем независимые параметры
        params = MathEngine.generate_parameters(template['parameters'])
        if not params:
            return None

        # 2. Универсальный поиск conditions (отдельное поле или внутри parameters)
        conditions = template.get('conditions')
        if not conditions:
            # Проверяем также внутри parameters (как часто бывает после импорта из JSON)
            conditions = template['parameters'].get('conditions') if 'conditions' in template['parameters'] else None

        # 3. Выполняем все условия
        if conditions:
            for expr in conditions.split(';'):
                expr = expr.strip()
                if not expr:
                    continue
                m = re.match(r'(\w+)\s*=\s*(.+)', expr)
                if m:
                    var, code = m.groups()
                    # Подставляем значения известных параметров в выражение
                    expr_for_eval = code
                    for p_name, p_val in params.items():
                        expr_for_eval = re.sub(rf'\b{p_name}\b', str(p_val), expr_for_eval)
                    try:
                        params[var] = eval(expr_for_eval)
                    except Exception as e:
                        print(f"Ошибка вычисления условия '{expr}': {e}")

        # 4. Формируем вопрос (заменяем все параметры в вопросе)
        question = template['question_template']
        for param, value in params.items():
            question = re.sub(rf"\{{{param}\}}", str(value), question)

        # 5. Формируем ответ
        answer_template = template['answer_template']

        # --- Тип ответа определяем автоматически
        answer_type = template.get('answer_type')
        if not answer_type:
            # Если в шаблоне ответа есть операторы, считаем что это формула
            if any(op in answer_template for op in '+-*/()'):
                answer_type = 'numeric'
            else:
                answer_type = 'string'

        if answer_type == 'string':
            answer = answer_template
            for param, value in params.items():
                answer = re.sub(rf"\{{{param}\}}", str(value), answer)
        else:
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
            'answer_type': answer_type
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))
