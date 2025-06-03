import re
from math_engine import MathEngine
import random

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template):
        """
        Генерирует вариант задания на основе шаблона
        Поддерживает как числовые, так и строковые ответы
        """
        # Проверка обязательных полей
        if not all(key in template for key in ['question_template', 'answer_template', 'parameters']):
            return None

        # Генерация параметров
        params = MathEngine.generate_parameters(template['parameters'])
        
        # Формирование вопроса
        question = template['question_template']
        for param, value in params.items():
            question = question.replace(f'{{{param}}}', str(value))
        
        # Вычисление ответа (многоступенчатая обработка)
        answer_template = template['answer_template']
        answer = None
        
        # 1. Пробуем вычислить как математическое выражение
        try:
            answer = MathEngine.evaluate_expression(answer_template, params)
        except:
            pass
        
        # 2. Если не получилось, пробуем как f-строку с вычислениями
        if answer is None:
            try:
                # Заменяем {A//10} на eval-выражения
                eval_template = re.sub(r'\{([^}]+)\}', 
                                    lambda m: str(eval(m.group(1), {}, params)), 
                                    answer_template)
                answer = eval_template
            except:
                pass
        
        # 3. Если все еще не получилось, просто форматируем как строку
        if answer is None:
            try:
                answer = answer_template.format(**params)
            except:
                answer = "Ошибка в формуле ответа"
        
        # Добавляем вычисленные параметры из conditions, если они есть
        if 'conditions' in template:
            try:
                # Выполняем условия для получения дополнительных параметров
                exec(template['conditions'], {}, params)
            except Exception as e:
                print(f"Error executing conditions: {e}")
        
        return {
            'question': question,
            'correct_answer': answer,
            'params': params,
            'template_id': template.get('id')
        }

    @staticmethod
    def extract_parameters(template_str):
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))