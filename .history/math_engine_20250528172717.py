import random
import re

class MathEngine:
    @staticmethod
    def generate_parameters(template_params):
        params = {}
        
        # Генерация основных параметров
        for param, config in template_params.items():
            if param == 'conditions':
                continue
                
            # Убедимся, что config - это словарь
            if not isinstance(config, dict):
                print(f"Некорректная конфигурация для параметра {param}: {config}")
                continue

            for _ in range(100):  # 100 попыток сгенерировать подходящее значение
                value = random.randint(config.get('min', 1), config.get('max', 10))
                
                # Проверка ограничений
                valid = True
                if 'constraints' in config:
                    for constraint in config['constraints']:
                        if constraint['type'] == 'multiple_of':
                            if value % constraint['value'] != 0:
                                valid = False
                        elif constraint['type'] == 'greater_than':
                            if 'param' in constraint:
                                if value <= params.get(constraint['param'], 0):
                                    valid = False
                            else:
                                if value <= constraint.get('value', 0):
                                    valid = False
                
                if valid:
                    params[param] = value
                    break
            else:
                params[param] = random.randint(config.get('min', 1), config.get('max', 10))
        
        # Проверка условий
        if 'conditions' in template_params:
            try:
                conditions = template_params['conditions']
                if not eval(conditions, {}, params):
                    return MathEngine.generate_parameters(template_params)
            except Exception as e:
                print(f"Ошибка проверки условий: {e}")
        
        return params

    @staticmethod
    def evaluate_expression(expr, params):
        try:
            # Заменяем все параметры в выражении
            for param, value in params.items():
                expr = expr.replace(f'{{{param}}}', str(value))
            
            # Удаляем оставшиеся фигурные скобки (для незамененных параметров)
            expr = re.sub(r'\{[A-Za-z]+\}', '1', expr)  # Заменяем на 1 чтобы не ломать вычисления
            
            # Безопасное вычисление
            return str(round(eval(expr), 2)) if '.' in expr else str(int(eval(expr)))
        except Exception as e:
            print(f"Ошибка вычисления: {expr} с параметрами {params}. Ошибка: {e}")
            return None