# math_engine.py
import random
import sympy
from sympy.parsing.sympy_parser import parse_expr
from sympy import symbols, simplify

class MathEngine:
    @staticmethod
    def generate_parameters(template_params):
        params = {}
        param_keys = list(template_params.keys())
        unresolved = set(param_keys)
        resolved = set()

        # 100 попыток сгенерировать валидный набор параметров
        for _ in range(100):
            generated = {}
            progress = True
            # Пробуем разрешить все параметры
            while unresolved and progress:
                progress = False
                for param in list(unresolved):
                    config = template_params[param]
                    if param == 'conditions':
                        unresolved.remove(param)
                        continue

                    def resolve_value(val):
                        if isinstance(val, str) and val.startswith('{') and val.endswith('}'):
                            dep = val.strip('{}')
                            return generated.get(dep)
                        return val

                    min_v = resolve_value(config.get('min', 0))
                    max_v = resolve_value(config.get('max', 1))
                    # Если зависимость ещё не разрешена — пропускаем этот проход
                    if (isinstance(min_v, str) and min_v.startswith('{')) or (isinstance(max_v, str) and max_v.startswith('{')):
                        continue

                    value = None
                    if config['type'] == 'int':
                        min_v = int(min_v)
                        max_v = int(max_v)
                        if min_v > max_v:
                            continue
                        value = random.randint(min_v, max_v)
                        # constraints
                        if 'constraints' in config:
                            for constraint in config['constraints']:
                                if constraint['type'] == 'multiple_of':
                                    mod = constraint['value']
                                    remainder = value % mod
                                    if remainder != 0:
                                        value += (mod - remainder)
                                        if value > max_v:
                                            value -= mod
                        value = int(value)
                    elif config['type'] == 'float':
                        min_v = float(min_v)
                        max_v = float(max_v)
                        if min_v > max_v:
                            continue
                        # constraints
                        step = config.get('constraints', [{}])[0].get('value', 0.01)
                        for c in config.get('constraints', []):
                            if c.get('type') == 'multiple_of':
                                step = c.get('value', 0.01)
                        steps = int(round((max_v - min_v) / step))
                        value = min_v + step * random.randint(0, steps)
                        value = round(value, str(step)[::-1].find('.'))
                    else:
                        # поддержка других типов если нужно
                        value = min_v
                    generated[param] = value
                    unresolved.remove(param)
                    resolved.add(param)
                    progress = True

            # Проверка conditions (если есть)
            valid = True
            conditions = template_params.get('conditions', '')
            if conditions:
                try:
                    valid = eval(conditions, {}, generated)
                except Exception:
                    valid = False
            if valid and len(unresolved) == 0:
                return generated
        return generated


    @staticmethod
def generate_parameters(template_params):
    if not template_params:
        return {}
    
    try:
        if isinstance(template_params, str):
            template_params = json.loads(template_params)
        # ... остальная логика генерации ...
    except Exception as e:
        print(f"Parameter generation error: {str(e)}")
        return {}
    @staticmethod
    def evaluate_expression(expr, params):
        try:
            # Заменяем параметры в выражении
            for param, value in params.items():
                expr = expr.replace(f'{{{param}}}', str(value))
            
            # Парсим выражение с помощью sympy
            parsed = parse_expr(expr, evaluate=True)
            
            # Если выражение содержит переменные - упрощаем
            if any(symbol in str(parsed) for symbol in ['x', 'y', 'z']):
                simplified = sympy.simplify(parsed)
                return str(simplified).replace('*', '')  # Убираем * для красоты
            
            # Для числовых выражений вычисляем значение
            return str(float(parsed.evalf()))
            
        except Exception as e:
            print(f"Error evaluating expression: {expr} with params {params}. Error: {e}")
            return None
