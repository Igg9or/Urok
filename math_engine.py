import sympy
from sympy.parsing.sympy_parser import parse_expr
import random

class MathEngine:
    @staticmethod
    def generate_parameters(template_params):
        params = {}
        # Пример: для параметра A с условиями
        for param, config in template_params.items():
            for _ in range(100):  # Попыток сгенерировать
                value = random.randint(config['min'], config['max'])
                if MathEngine._check_constraints(param, value, config.get('constraints', []), params):
                    params[param] = value
                    break
        return params

    @staticmethod
    def _check_constraints(param, value, constraints, existing_params):
        for constraint in constraints:
            if constraint['type'] == 'multiple_of' and value % constraint['value'] != 0:
                return False
            elif constraint['type'] == 'greater_than':
                other = existing_params.get(constraint['param'], constraint.get('value'))
                if value <= other:
                    return False
        return True

    @staticmethod
    def evaluate_expression(expr, params):
        try:
            # Безопасный eval с sympy
            local_dict = {k: sympy.Integer(v) if isinstance(v, int) else sympy.Float(v) 
                         for k, v in params.items()}
            return str(parse_expr(expr, local_dict=local_dict).evalf())
        except:
            return None