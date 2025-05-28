import random
import sympy
from sympy.parsing.sympy_parser import parse_expr

class MathEngine:
    @staticmethod
    def generate_parameters(template_params):
        params = {}
        conditions = template_params.get('conditions', '')
        
        # Удаляем conditions из параметров, если есть
        param_configs = {k: v for k, v in template_params.items() if k != 'conditions'}
        
        for _ in range(100):  # Максимум 100 попыток
            generated = {}
            valid = True
            
            # Генерация параметров
            for param, config in param_configs.items():
                if config['type'] == 'int':
                    value = random.randint(config['min'], config['max'])
                    
                    # Проверка ограничений
                    if 'constraints' in config:
                        for constraint in config['constraints']:
                            if constraint['type'] == 'multiple_of':
                                if value % constraint['value'] != 0:
                                    valid = False
                            elif constraint['type'] == 'greater_than':
                                if 'param' in constraint:
                                    if value <= generated.get(constraint['param'], 0):
                                        valid = False
                                else:
                                    if value <= constraint['value']:
                                        valid = False
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
        
        return generated

    @staticmethod
    def evaluate_expression(expr, params):
        try:
            # Заменяем параметры в выражении на их значения
            for param, value in params.items():
                expr = expr.replace(f'{param}', str(value))
            
            # Безопасный eval с sympy
            return str(parse_expr(expr, evaluate=True))
        except Exception as e:
            print(f"Error evaluating expression: {expr} with params {params}. Error: {e}")
            return None