# math_engine.py
import random
import sympy
from sympy.parsing.sympy_parser import parse_expr

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
    try:
        # Если выражение содержит параметры в фигурных скобках - форматируем как строку
        if isinstance(expr, str) and any(f'{{{key}}}' in expr for key in params):
            # Вычисляем все параметры, которые могут быть выражениями
            computed_params = {}
            for key, value in params.items():
                if isinstance(value, str) and any(f'{{{k}}}' in value for k in params):
                    # Рекурсивно вычисляем вложенные выражения
                    computed_params[key] = MathEngine.evaluate_expression(value, params)
                else:
                    computed_params[key] = value
            
            # Форматируем строку с вычисленными параметрами
            return expr.format(**computed_params)
        
        # Оригинальная логика для математических выражений
        local_dict = {k: sympy.Integer(v) if isinstance(v, int) else sympy.Float(v) 
                     for k, v in params.items()}
        return str(parse_expr(expr, local_dict=local_dict).evalf())
    except Exception as e:
        print(f"Error evaluating expression: {expr} with params {params}. Error: {e}")
        return None