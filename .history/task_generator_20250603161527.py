import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        params = MathEngine.generate_parameters(template['parameters'])
        
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))
        
        if template.get('answer_type') == 'string':
            answer = template['answer_template'].format(**params)
        else:
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