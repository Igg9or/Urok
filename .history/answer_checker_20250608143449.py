# answer_checker.py
import re
from sympy import simplify, sympify, N
from math_engine import MathEngine

class AnswerChecker:
    @staticmethod
    def normalize_string(s):
        """Унификация строковых ответов"""
        return ''.join(str(s).lower().split()).replace(',', '.')

    @staticmethod
    def check_percent(user, correct):
        """Проверка процентных ответов"""
        def to_float(s):
            try:
                return float(re.sub(r'[^\d.]', '', str(s)))
            except:
                return None
        
        user_num = to_float(user)
        correct_num = to_float(correct)
        if None in (user_num, correct_num):
            return False
        return abs(user_num - correct_num) < 0.05

    @staticmethod
    def check_numeric(user, correct, tolerance=0.001):
        """Проверка числовых ответов с поддержкой дробей"""
        try:
            # Пробуем вычислить оба значения
            user_val = MathEngine.normalize_answer(user)
            correct_val = MathEngine.normalize_answer(correct)
            
            # Сравнение с допуском
            return abs(float(user_val) - float(correct_val)) < tolerance
        except:
            return False

    @staticmethod
    def check_list(user, correct):
        """Проверка списков значений"""
        def parse_list(s):
            parts = re.split(r'[;,\s]+', str(s).strip())
            return [MathEngine.normalize_answer(p) for p in parts if p]
        
        try:
            user_vals = parse_list(user)
            correct_vals = parse_list(correct)
            return (len(user_vals) == len(correct_vals) and 
                   all(abs(u - c) < 0.01 for u, c in zip(user_vals, correct_vals))
        except:
            return False

    @staticmethod
    def check_algebraic(user, correct):
        """Проверка алгебраических выражений"""
        try:
            user_expr = sympify(user)
            correct_expr = sympify(correct)
            return simplify(user_expr - correct_expr) == 0
        except:
            return AnswerChecker.normalize_string(user) == AnswerChecker.normalize_string(correct)

    @classmethod
    def check_answer(cls, user_answer, correct_answer, answer_type='numeric'):
        """Основной метод проверки"""
        user = str(user_answer).strip()
        correct = str(correct_answer).strip()

        # Процентные ответы имеют приоритет
        if '%' in user or '%' in correct:
            return cls.check_percent(user, correct)

        # Выбор стратегии проверки
        if answer_type == 'string':
            return cls.normalize_string(user) == cls.normalize_string(correct)
        elif answer_type == 'algebraic':
            return cls.check_algebraic(user, correct)
        elif answer_type == 'list':
            return cls.check_list(user, correct)
        else:  # numeric
            return cls.check_numeric(user, correct)