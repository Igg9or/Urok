import re
from math_engine import MathEngine

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        """
        Генерирует вариант задания на основе шаблона
        """
        # Генерация параметров
        params = MathEngine.generate_parameters(template['parameters'])
        if not params:
            return None
        
        # Формирование вопроса
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))
        
        # Вычисление ответа
        answer = MathEngine.evaluate_expression(template['answer_template'], params)
        
        if answer is None:
            return None
            
        return {
            'question': question,
            'correct_answer': answer,
            'params': params,
            'template_id': template.get('id')
        }

    @staticmethod
    def validate_template(template):
        """Проверяет, можно ли сгенерировать задание по шаблону"""
        try:
            variant = TaskGenerator.generate_task_variant(template)
            return variant is not None
        except:
            return False