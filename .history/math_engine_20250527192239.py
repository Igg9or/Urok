import random

class MathEngine:
    @staticmethod
    def generate_parameters(template_params):
        params = {}
        
        # Удаляем conditions из параметров, если есть
        param_configs = {k: v for k, v in template_params.items() if k != 'conditions'}
        
        for param, config in param_configs.items():
            # Генерация значения с учетом ограничений
            for _ in range(100):  # Максимум 100 попыток
                value = random.randint(config['min'], config['max'])
                
                # Проверка ограничений
                valid = True
                if 'constraints' in config:
                    for constraint in config['constraints']:
                        if constraint['type'] == 'multiple_of':
                            if value % constraint['value'] != 0:
                                valid = False
                        elif constraint['type'] == 'greater_than':
                            if value <= params.get(constraint.get('param'), constraint.get('value', 0)):
                                valid = False
                
                if valid:
                    params[param] = value
                    break
            
            if param not in params:  # Если не удалось сгенерировать
                params[param] = random.randint(config['min'], config['max'])
        
        # Проверка условий
        if 'conditions' in template_params:
            try:
                if not eval(template_params['conditions'], {}, params):
                    # Если условия не выполнены, генерируем заново основные параметры
                    return MathEngine.generate_parameters(template_params)
            except:
                pass
        
        return params

    @staticmethod
    def evaluate_expression(expr, params):
        try:
            # Подставляем параметры в выражение
            for param, value in params.items():
                expr = expr.replace(f'{{{param}}}', str(value))
            
            # Безопасный eval
            return str(eval(expr, {'__builtins__': None}, params))
        except Exception as e:
            print(f"Error evaluating: {expr} with {params}. Error: {e}")
            return None