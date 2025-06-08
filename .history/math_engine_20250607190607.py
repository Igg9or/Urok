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
        # 1. Собираем все ключи типа choice для согласованного выбора
        choice_keys = [param for param, config in template_params.items() if isinstance(config, dict) and config.get('type') == 'choice']
        choice_len = None
        if len(choice_keys) >= 2:
            # Проверяем, что длины списков совпадают
            lengths = [len(template_params[k]['values']) for k in choice_keys]
            if len(set(lengths)) == 1:
                choice_len = lengths[0]

        for _ in range(100):  # Максимум 100 попыток
            generated = {}
            valid = True

            # Генерация согласованных choice-параметров по индексу
            if choice_len:
                idx = random.randrange(choice_len)
                for k in choice_keys:
                    generated[k] = template_params[k]['values'][idx]

            # Генерация остальных параметров
            for param, config in template_params.items():
                if param == 'conditions' or (choice_len and param in choice_keys):
                    continue

                if config['type'] == 'int':
                    value = random.randint(config['min'], config['max'])
                    # Применяем ограничения
                    if 'constraints' in config:
                        for constraint in config['constraints']:
                            if constraint['type'] == 'multiple_of':
                                remainder = value % constraint['value']
                                if remainder != 0:
                                    value += (constraint['value'] - remainder)
                                    if value > config['max']:
                                        value -= constraint['value']
                    generated[param] = value
                    
                elif config['type'] == 'float':
                    min_v = config.get('min', 0)
                    max_v = config.get('max', 1)
                    step = config.get('constraints', [{}])[0].get('value', 0.01)
                    # step ищем первый multiple_of или default=0.01
                    for c in config.get('constraints', []):
                        if c.get('type') == 'multiple_of':
                            step = c.get('value', 0.01)
                    steps = int(round((max_v - min_v) / step))
                    value = min_v + step * random.randint(0, steps)
                    value = round(value, str(step)[::-1].find('.'))
                    generated[param] = value

                elif config['type'] == 'choice':
                    # Одиночные choice (не согласованные)
                    generated[param] = random.choice(config['values'])

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
    def normalize_answer(answer):
        """Приводит ответ к числовому виду, обрабатывая дроби и другие формы"""
        try:
            # Если ответ уже число - возвращаем как есть
            if isinstance(answer, (int, float)):
                return float(answer)
                
            # Обработка дробей вида a/b
            if '/' in answer:
                numerator, denominator = answer.split('/')
                return float(numerator) / float(denominator)
                
            # Обработка десятичных дробей с запятой
            if ',' in answer:
                return float(answer.replace(',', '.'))
                
            # Стандартное преобразование
            return float(answer)
        except (ValueError, TypeError):
            # Если не удалось преобразовать в число, возвращаем исходный ответ
            return answer
    
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
