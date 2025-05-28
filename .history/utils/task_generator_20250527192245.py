import re
from math_engine import MathEngine

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        # Генерация параметров
        params = MathEngine.generate_parameters(template['parameters'])
        
        # Замена в вопросе
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))
        
        # Вычисление ответа
        answer = MathEngine.evaluate_expression(template['answer_template'], params)
        
        return {
            'question': question,
            'correct_answer': answer,
            'params': params,
            'template_id': template.get('id')
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))