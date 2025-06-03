# math_engine.py
import random
import sympy
from sympy.parsing.sympy_parser import parse_expr
from sympy import symbols, simplify

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
    @staticmethod
    def evaluate_expression(expr, params):
        try:
            if any(c in expr for c in ['x', 'y', 'z']):  # Если есть переменные
                # Создаем символы для переменных
                vars_in_expr = set(re.findall(r'[a-zA-Z]', expr)) - set(params.keys())
                syms = symbols(' '.join(vars_in_expr))
                local_dict = {**{k: v for k, v in params.items()}, 
                             **{str(s): s for s in syms}}
                
                # Упрощаем выражение
                simplified = str(simplify(parse_expr(expr, local_dict=local_dict))
                return simplified.replace('*', '')  # Убираем * для красоты
            else:
                # Старая логика для числовых выражений
                local_dict = {k: sympy.Integer(v) if isinstance(v, int) else sympy.Float(v) 
                            for k, v in params.items()}
                return str(parse_expr(expr, local_dict=local_dict).evalf())
        except Exception as e:
            print(f"Error evaluating expression: {expr} with params {params}. Error: {e}")
            return None
