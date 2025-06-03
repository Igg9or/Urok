# math_engine.py
import random
import sympy
from sympy.parsing.sympy_parser import parse_expr
import re

def detect_answer_type(answer_template):
    """Автоматически определяет тип ответа по шаблону"""
    if not isinstance(answer_template, str):
        return 'numeric'
    
    # Проверка на статический текст
    if '{' not in answer_template and '}' not in answer_template:
        return 'static'
    
    # Проверка на чистые подстановки переменных
    if re.fullmatch(r'^(\{[A-Za-z_]\w*\}[^\{\}]*)+$', answer_template):
        return 'string_template'
    
    # Проверка на математические выражения
    if re.fullmatch(r'^[\d\s\+\-\*\/%\(\)\.\{\}]+$', answer_template.replace(' ', '')):
        return 'numeric'
    
    # Во всех остальных случаях - смешанный тип
    return 'mixed'

class MathEngine:
    @staticmethod
    def generate_parameters(template_params):
        params = {}
        conditions = template_params.get('conditions', '')
        
        for _ in range(100):  # Максимум 100 попыток
            generated = {}
            valid = True
            
            # Генерация параметров с учетом ограничений
            for param, config in template_params.items():
                if param == 'conditions':
                    continue
                    
                if config['type'] == 'int':
                    value = random.randint(config['min'], config['max'])
                    
                    # Применяем ограничения
                    if 'constraints' in config:
                        for constraint in config['constraints']:
                            if constraint['type'] == 'multiple_of':
                                # Корректируем значение чтобы было кратно
                                remainder = value % constraint['value']
                                if remainder != 0:
                                    value += (constraint['value'] - remainder)
                                    # Проверяем не вышли ли за границы
                                    if value > config['max']:
                                        value -= constraint['value']
                    generated[param] = value
            
            # Проверка условий
            if valid and conditions:
                try:
                    if not eval(conditions, {}, generated):
                        valid = False
                except:
                    valid = False
            
            if valid:
                return generated
        
        # Если не удалось сгенерировать - возвращаем последний вариант
        return generated

   
    @staticmethod
    def evaluate_expression(expr, params):
        """Вычисляет выражение с автоматическим определением типа"""
        if not isinstance(expr, str):
            return str(expr)
        
        answer_type = detect_answer_type(expr)
        
        try:
            if answer_type == 'static':
                return expr
            
            if answer_type == 'string_template':
                return expr.format(**params)
            
            if answer_type == 'numeric':
                # Безопасное вычисление математического выражения
                return str(eval(expr, {}, params))
            
            if answer_type == 'mixed':
                # Обработка смешанного типа
                def eval_match(match):
                    inner_expr = match.group(1)
                    try:
                        return str(eval(inner_expr, {}, params))
                    except:
                        return match.group(0)  # Возвращаем оригинал при ошибке
                return re.sub(r'\{(.+?)\}', eval_match, expr)
                
        except Exception as e:
            print(f"Error evaluating expression: {expr} with params {params}. Error: {e}")
            return None