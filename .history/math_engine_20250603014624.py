# math_engine.py
import random
import sympy
from sympy.parsing.sympy_parser import parse_expr
import re

def detect_answer_type(answer_template):
    """Автоматически определяет тип ответа по шаблону"""
    if not isinstance(answer_template, str):
        return 'numeric'
    
    # Проверка на статический текст
    if '{' not in answer_template and '}' not in answer_template:
        return 'static'
    
    # Проверка на чистые подстановки переменных
    if re.fullmatch(r'^(\{[A-Za-z_]\w*\}[^\{\}]*)+$', answer_template):
        return 'string_template'
    
    # Проверка на математические выражения
    if re.fullmatch(r'^[\d\s\+\-\*\/%\(\)\.\{\}]+$', answer_template.replace(' ', '')):
        return 'numeric'
    
    # Во всех остальных случаях - смешанный тип
    return 'mixed'

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
        """Улучшенная версия с автоматическим определением типа"""
        if not isinstance(expr, str):
            return str(expr)
        
        # Статический текст без подстановок
        if '{' not in expr and '}' not in expr:
            return expr
        
        try:
            # Попытка обработки как строкового шаблона
            if all(isinstance(params.get(match.group(1), (int, float)) 
            for match in re.finditer(r'\{([A-Za-z_]\w*)\}', expr)):
                return expr.format(**params)
            
            # Обработка математических выражений
            if re.fullmatch(r'^[\d\s\+\-\*\/%\(\)\.\{\}]+$', expr.replace(' ', '')):
                return str(eval(expr, {}, params))
            
            # Смешанный режим: текст + выражения
            def eval_match(match):
                try:
                    return str(eval(match.group(1), {}, params)
                except:
                    return match.group(0)
                    
            return re.sub(r'\{(.+?)\}', eval_match, expr)
            
        except Exception as e:
            print(f"Evaluation error: {expr} with {params}. Error: {e}")
            return None