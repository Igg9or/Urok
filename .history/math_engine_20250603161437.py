# math_engine.py
import random
import sympy
from sympy.parsing.sympy_parser import parse_expr

class MathEngine:
    
    @staticmethod
    def generate_parameters(template_params):
        params = {}
        conditions = template_params.get('conditions', '')
        derived = template_params.get('derived', {})
        
        for _ in range(100):  # Максимум 100 попыток
            generated = {}
            valid = True
            
            # Генерация основных параметров
            for param, config in template_params.items():
                if param in ['conditions', 'derived']:
                    continue
                    
                if config['type'] == 'int':
                    value = random.randint(config['min'], config['max'])
                    
                    if 'constraints' in config:
                        for constraint in config['constraints']:
                            if constraint['type'] == 'multiple_of':
                                remainder = value % constraint['value']
                                if remainder != 0:
                                    value += (constraint['value'] - remainder)
                                    if value > config['max']:
                                        value -= constraint['value']
                    generated[param] = value
            
            # Вычисляем derived-переменные
            try:
                for var, expr in derived.items():
                    generated[var] = eval(expr, {}, generated)
            except:
                valid = False
            
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
            # Если это строка с подстановкой, просто форматируем
            if any(f'{{{p}}}' in expr for p in params):
                return expr.format(**params)
            
            # Иначе вычисляем как выражение
            local_dict = {k: sympy.Integer(v) if isinstance(v, int) else sympy.Float(v) 
                         for k, v in params.items()}
            return str(parse_expr(expr, local_dict=local_dict).evalf())
        except Exception as e:
            print(f"Error evaluating expression: {expr} with params {params}. Error: {e}")
            return None