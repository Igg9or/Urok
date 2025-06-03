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
        # Если это строка с параметрами в фигурных скобках
        if isinstance(expr, str) and '{' in expr:
            # Сначала вычисляем выражения вида {A//10}
            def eval_expr(match):
                try:
                    return str(eval(match.group(1), {}, params)
                except:
                    return match.group(0)
            
            expr = re.sub(r'\{([^}]+)\}', eval_expr, expr)
            
            # Затем подставляем простые параметры
            return expr.format(**params)
        
        # Стандартная обработка математических выражений
        local_dict = {k: sympy.Integer(v) for k, v in params.items()}
        return str(parse_expr(expr, local_dict=local_dict).evalf())
    except Exception as e:
        print(f"Error evaluating: {expr} with {params}. Error: {e}")
        return "Ошибка в формуле ответа"