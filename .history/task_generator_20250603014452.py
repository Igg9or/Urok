import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
        def generate_task_variant(template):
        """
        Генерирует вариант задания на основе шаблона
        с автоматическим определением типа ответа
        """
        # Проверяем наличие обязательных полей
        if not all(key in template for key in ['question_template', 'answer_template', 'parameters']):
            return None

        # Генерация параметров
        params = MathEngine.generate_parameters(
            template['parameters'] if isinstance(template['parameters'], dict)
            else json.loads(template['parameters'])
        )

        # Формирование вопроса
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))

        # Обработка условий (если есть)
        if 'conditions' in template and template['conditions']:
            try:
                # Выполняем условия для вычисления производных параметров
                exec(template['conditions'], {}, params)
            except Exception as e:
                print(f"Error executing conditions: {e}")

        # Генерация ответа с автоматическим определением типа
        answer = MathEngine.evaluate_expression(template['answer_template'], params)

        return {
            'question': question,
            'correct_answer': answer if answer is not None else "Ошибка в шаблоне ответа",
            'params': params,
            'template_id': template.get('id')
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))