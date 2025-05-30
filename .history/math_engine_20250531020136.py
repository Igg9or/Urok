# math_engine.py
import random
import sympy
from sympy.parsing.sympy_parser import parse_expr
import re
from typing import Dict, Any, Tuple

class MathEngine:
    # Словари для преобразования чисел в слова
    NUMBER_WORDS = {
        0: 'ноль', 1: 'один', 2: 'два', 3: 'три', 4: 'четыре',
        5: 'пять', 6: 'шесть', 7: 'семь', 8: 'восемь', 9: 'девять',
        10: 'десять', 20: 'двадцать', 30: 'тридцать', 40: 'сорок',
        50: 'пятьдесят', 60: 'шестьдесят', 70: 'семьдесят',
        80: 'восемьдесят', 90: 'девяносто',
        100: 'сто', 200: 'двести', 300: 'триста', 400: 'четыреста',
        500: 'пятьсот', 600: 'шестьсот', 700: 'семьсот',
        800: 'восемьсот', 900: 'девятьсот'
    }

    SCALE_WORDS = [
        ('тысяч', 'тысяча', 'тысячи'),
        ('миллионов', 'миллион', 'миллиона'),
        ('миллиардов', 'миллиард', 'миллиарда')
    ]

    @staticmethod
    def number_to_words(num: int) -> str:
        """Конвертирует число в его текстовое представление на русском"""
        if num == 0:
            return MathEngine.NUMBER_WORDS[0]
        
        parts = []
        scale_idx = -1
        
        while num > 0:
            chunk = num % 1000
            num = num // 1000
            scale_idx += 1
            
            if chunk == 0:
                continue
                
            words = []
            hundreds = chunk // 100
            tens = chunk % 100
            
            if hundreds > 0:
                words.append(MathEngine.NUMBER_WORDS[hundreds * 100])
            
            if 10 <= tens < 20:
                words.append(MathEngine.NUMBER_WORDS[tens])
            else:
                tens_part = (tens // 10) * 10
                units = tens % 10
                
                if tens_part > 0:
                    words.append(MathEngine.NUMBER_WORDS[tens_part])
                if units > 0:
                    words.append(MathEngine.NUMBER_WORDS[units])
            
            if scale_idx >= 0 and scale_idx < len(MathEngine.SCALE_WORDS):
                scale = MathEngine.SCALE_WORDS[scale_idx]
                if tens % 100 in (11, 12, 13, 14):
                    words.append(scale[0])
                elif tens % 10 == 1:
                    words.append(scale[1])
                elif 2 <= tens % 10 <= 4:
                    words.append(scale[2])
                else:
                    words.append(scale[0])
            
            parts.insert(0, ' '.join(words))
        
        return ' '.join(parts)

    @staticmethod
    def words_to_number(text: str) -> int:
        """Конвертирует текстовое представление числа в числовое"""
        # Реализация этого метода потребует более сложной обработки
        # Для простоты можно использовать заранее подготовленные шаблоны
        # В реальной реализации нужно разбирать текст и вычислять число
        return 0  # Заглушка

    @staticmethod
    def format_number_with_spaces(num: int) -> str:
        """Форматирует число с пробелами между классами"""
        return "{:,}".format(num).replace(",", " ")

    @staticmethod
    def get_digit_position(num: int, digit: int) -> str:
        """Возвращает позицию цифры в числе (единицы, десятки и т.д.)"""
        s = str(num)
        pos = s.find(str(digit))
        if pos == -1:
            return "отсутствует"
        
        length = len(s)
        positions = [
            "единицы", "десятки", "сотни", 
            "тысячи", "десятки тысяч", "сотни тысяч",
            "миллионы", "десятки миллионов", "сотни миллионов",
            "миллиарды", "десятки миллиардов", "сотни миллиардов"
        ]
        return positions[length - pos - 1]

    @staticmethod
    def generate_parameters(template_params: Dict[str, Any]) -> Dict[str, Any]:
        """Генерирует параметры с учетом условий и ограничений"""
        params = {}
        conditions = template_params.get('conditions', '')
        
        for _ in range(100):  # Максимум 100 попыток генерации
            generated = {}
            valid = True
            
            for param, config in template_params.items():
                if param == 'conditions':
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
                    # Подготавливаем дополнительные вычисления
                    context = {
                        **generated,
                        'str': str,
                        'len': len,
                        'int': int
                    }
                    
                    if not eval(conditions, {}, context):
                        valid = False
                except:
                    valid = False
            
            if valid:
                # Добавляем вычисляемые поля
                for param, value in generated.items():
                    # Позиции цифр
                    if '_pos' in conditions or '_pos' in ''.join(template_params.keys()):
                        s = str(value)
                        for i, d in enumerate(s):
                            generated[f"{param}_{d}_pos"] = MathEngine.get_digit_position(value, int(d))
                
                return generated
        
        # Если не удалось сгенерировать - возвращаем последний вариант
        return generated

    @staticmethod
    def evaluate_expression(expr: str, params: Dict[str, Any]) -> str:
        """Вычисляет выражение с подстановкой параметров"""
        try:
            # Специальная обработка для текстовых представлений
            if '_word' in expr:
                num = eval(expr.split('_word')[0].strip('{}'), {}, params)
                return MathEngine.number_to_words(num)
            
            # Специальная обработка для форматирования чисел
            if '_formatted' in expr:
                num = eval(expr.split('_formatted')[0].strip('{}'), {}, params)
                return MathEngine.format_number_with_spaces(num)
            
            # Специальная обработка для чтения чисел
            if '_read' in expr:
                num = eval(expr.split('_read')[0].strip('{}'), {}, params)
                return MathEngine.number_to_words(num)
            
            # Обычное вычисление
            local_dict = {k: sympy.Integer(v) if isinstance(v, int) else sympy.Float(v) 
                         for k, v in params.items()}
            return str(parse_expr(expr, local_dict=local_dict).evalf())
        except Exception as e:
            print(f"Error evaluating expression: {expr} with params {params}. Error: {e}")
            return None