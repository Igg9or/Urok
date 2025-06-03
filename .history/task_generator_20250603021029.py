import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        """
        Генерирует вариант задания на основе шаблона
        с поддержкой текстовых ответов вида "X дм Y см"
        """
        # Проверка обязательных полей
        required_fields = ['question_template', 'answer_template', 'parameters']
        if not all(key in template for key in required_fields):
            return None

        # Генерация параметров
        params = MathEngine.generate_parameters(template['parameters'])
        
        # Обработка условий (если есть)
        if 'conditions' in template:
            try:
                # Создаем локальный контекст для выполнения условий
                local_vars = params.copy()
                exec(template['conditions'], {}, local_vars)
                # Обновляем параметры вычисленными значениями
                params.update({k: v for k, v in local_vars.items() 
                            if k not in ['__builtins__']})
            except Exception as e:
                print(f"Error executing conditions: {e}")

        # Формирование вопроса
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))
        
        # Обработка ответа
        answer_template = template['answer_template']
        answer = None
        
        # 1. Пробуем вычислить как f-строку с параметрами
        try:
            # Сначала вычисляем все выражения внутри фигурных скобок
            def eval_match(match):
                expr = match.group(1)
                try:
                    return str(eval(expr, {}, params))
                except:
                    return match.group(0)
                    
            evaluated = re.sub(r'\{([^}]+)\}', eval_match, answer_template)
            answer = evaluated
        except Exception as e:
            print(f"Error evaluating answer template: {e}")
            answer = "Ошибка в формуле ответа"
        
        return {
            'question': question,
            'correct_answer': answer,
            'params': params,
            'template_id': template.get('id')
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))