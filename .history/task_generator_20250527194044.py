import re
from math_engine import MathEngine

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
        missing_params = []
        for param in TaskGenerator.extract_parameters(question):
            if param in params:
                question = question.replace(f'{{{param}}}', str(params[param]))
            else:
                missing_params.append(param)
        
        # Если есть незамененные параметры - генерируем для них значения
        for param in missing_params:
            value = random.randint(1, 10)  # Значения по умолчанию
            params[param] = value
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