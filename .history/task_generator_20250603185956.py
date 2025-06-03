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

        # === Обработка conditions ===
        # Если в шаблоне есть условия (вычисление зависимых переменных)
        conditions = template.get('conditions')
        if conditions:
            # conditions могут быть типа "dm = A // 10; cm = A % 10"
            for expr in conditions.split(';'):
                expr = expr.strip()
                if not expr:
                    continue
                m = re.match(r'(\w+)\s*=\s*(.+)', expr)
                if m:
                    var, code = m.groups()
                    # Подставляем уже сгенерированные params в выражение
                    expr_for_eval = code
                    for p_name, p_val in params.items():
                        expr_for_eval = re.sub(rf'\b{p_name}\b', str(p_val), expr_for_eval)
                    try:
                        params[var] = eval(expr_for_eval)
                    except Exception as e:
                        print(f"Ошибка вычисления условия '{expr}': {e}")

        # Подставляем параметры в шаблон вопроса
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))

        answer_template = template['answer_template']
        answer_type = template.get('answer_type')
if not answer_type:
    # Определяем тип по шаблону: если есть операторы — numeric, иначе string
    if any(op in template['answer_template'] for op in '+-*/()'):
        answer_type = 'numeric'
    else:
        answer_type = 'string'

if answer_type == 'string':
    answer = template['answer_template']
    for param, value in params.items():
        answer = answer.replace(f'{{{param}}}', str(value))
else:
    try:
        answer = str(eval(template['answer_template'].format(**params)))
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
