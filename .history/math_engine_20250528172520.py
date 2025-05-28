import random
import re

class MathEngine:
    @staticmethod
    def generate_parameters(template_params, max_attempts=100):
        params = {}
        
        # Проверяем, что template_params - словарь
        if not isinstance(template_params, dict):
            return {}

        # Генерация параметров с учетом ограничений
        for param, config in template_params.items():
            if param == 'conditions':
                continue
                
            if not isinstance(config, dict):
                continue

            for _ in range(max_attempts):
                # Обрабатываем кратные значения
                if 'multiple_of' in config.get('constraints', []):
                    step = config['constraints']['multiple_of']
                    min_val = config['min']
                    max_val = config['max']
                    value = random.randint(min_val // step, max_val // step) * step
                else:
                    value = random.randint(config['min'], config['max'])
                
                params[param] = value
                break
            else:
                params[param] = config['min']  # fallback

        # Проверка условий
        if 'conditions' in template_params:
            conditions = template_params['conditions']
            try:
                if not eval(conditions, {}, params):
                    # Если условия не выполнены - пробуем снова
                    return MathEngine.generate_parameters(template_params, max_attempts-1)
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