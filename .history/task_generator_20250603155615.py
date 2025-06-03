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
    
    # Вычисляем дополнительные параметры из conditions, если они есть
    if 'conditions' in template and template['conditions']:
        try:
            # Безопасное выполнение условий
            exec(template['conditions'], {}, params)
        except Exception as e:
            print(f"Error evaluating conditions: {e}")
    
    # Формирование вопроса
    question = template['question_template']
    for param, value in params.items():
        question = question.replace(f'{{{param}}}', str(value))
    
    # Вычисление ответа (поддерживает как математические выражения, так и строки)
    computed_answer = MathEngine.evaluate_expression(template['answer_template'], params)
    
    return {
        'question': question,
        'correct_answer': computed_answer,
        'params': params,
        'template_id': template.get('id')
    }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))