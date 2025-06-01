from asteval import Interpreter
import random
import logging
from typing import Dict, Any, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafeMathEngine:
    def __init__(self):
        """Инициализация безопасного интерпретатора математических выражений"""
        self.aeval = Interpreter(
            usersyms={
                'random': random,
                'randint': random.randint,
                'round': round,
                'abs': abs,
                'min': min,
                'max': max
            },
            no_print=True,
            no_raise=False
        )
        self.aeval.symtable['__builtins__'] = None  # Отключаем встроенные функции
    
    def evaluate_expression(self, expr: str, params: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """
        Безопасное вычисление математического выражения
        :param expr: Строка с математическим выражением
        :param params: Словарь с параметрами для подстановки
        :return: Результат вычисления или None при ошибке
        """
        if not expr:
            return None

        try:
            if params:
                for k, v in params.items():
                    self.aeval.symtable[k] = v
            
            result = self.aeval(expr)
            if result is None:
                return None
                
            return float(result)
        except Exception as e:
            logger.error(f"Error evaluating expression '{expr}': {str(e)}")
            return None

    def validate_condition(self, condition: str, params: Dict[str, Any]) -> bool:
        """
        Проверка условия с параметрами
        :param condition: Условие для проверки
        :param params: Параметры для подстановки
        :return: True если условие выполнено, False если нет или при ошибке
        """
        if not condition:
            return True
            
        try:
            result = self.evaluate_expression(condition, params)
            return result is not None and bool(result)
        except:
            return False


class ParameterGenerator:
    MAX_ATTEMPTS = 1000

    @classmethod
    def generate_parameters(
        cls, 
        parameters_config: Dict[str, Any], 
        condition: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Генерация параметров по конфигурации с учетом условий
        :param parameters_config: Конфигурация параметров
        :param condition: Дополнительное условие для проверки
        :return: Словарь с параметрами или None если не удалось сгенерировать
        """
        math_engine = SafeMathEngine()
        
        for attempt in range(cls.MAX_ATTEMPTS):
            params = {}
            valid = True

            # 1. Генерация параметров по конфигурации
            for param_name, config in parameters_config.items():
                if param_name == 'conditions':
                    continue
                    
                param_value = cls._generate_single_param(config, params)
                if param_value is None:
                    valid = False
                    break
                    
                params[param_name] = param_value

            # 2. Проверка дополнительного условия
            if valid and condition:
                valid = math_engine.validate_condition(condition, params)

            if valid:
                return params

        logger.warning(f"Failed to generate parameters after {cls.MAX_ATTEMPTS} attempts")
        return None

    @staticmethod
    def _generate_single_param(config: Dict[str, Any], existing_params: Dict[str, Any]) -> Any:
        """
        Генерация одного параметра с учетом ограничений
        """
        param_type = config.get('type', 'int')
        constraints = config.get('constraints', [])
        min_val = config.get('min', 0)
        max_val = config.get('max', 10)

        # Базовая генерация значения
        if param_type == 'int':
            value = random.randint(min_val, max_val)
        elif param_type == 'float':
            value = random.uniform(min_val, max_val)
        else:
            value = None

        # Применение ограничений
        for constraint in constraints:
            if isinstance(constraint, str):
                if constraint.startswith('multiple_of'):
                    base = int(constraint.split('_')[-1])
                    remainder = value % base
                    if remainder != 0:
                        value += (base - remainder)
                        if value > max_val:
                            value -= base
                elif constraint.startswith('greater_than'):
                    other_param = constraint.split('_')[-1]
                    if other_param in existing_params:
                        value = max(value, existing_params[other_param] + 1)
                elif constraint.startswith('less_than'):
                    other_param = constraint.split('_')[-1]
                    if other_param in existing_params:
                        value = min(value, existing_params[other_param] - 1)
        
        return value


# Глобальные экземпляры для использования
math_engine = SafeMathEngine()
parameter_generator = ParameterGenerator()

# Для обратной совместимости
class MathEngine:
    @staticmethod
    def generate_parameters(template_params):
        return parameter_generator.generate_parameters(template_params)
    
    @staticmethod
    def evaluate_expression(expr, params=None):
        return math_engine.evaluate_expression(expr, params)