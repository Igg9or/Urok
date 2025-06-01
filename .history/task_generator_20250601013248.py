from math_engine import math_engine, parameter_generator
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TaskGenerator:
    @staticmethod
    def generate_task_variant(template: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Генерация варианта задания по шаблону
        :param template: Шаблон задания
        :return: Словарь с заданием или None при ошибке
        """
        if not TaskGenerator._validate_template(template):
            return None

        try:
            # 1. Извлечение параметров из шаблона
            parameters_config = template.get('parameters', {})
            condition = template.get('validation', {}).get('expression', '')

            # 2. Генерация параметров
            params = parameter_generator.generate_parameters(parameters_config, condition)
            if not params:
                logger.error("Failed to generate parameters")
                return None

            # 3. Генерация вопроса
            question = TaskGenerator._generate_question(template['question_template'], params)
            if not question:
                return None

            # 4. Вычисление ответа
            answer = math_engine.evaluate_expression(template['answer_template'], params)
            if answer is None:
                return None

            # 5. Формирование результата
            return {
                'question': question,
                'correct_answer': str(answer),
                'params': params,
                'template_id': template.get('id'),
                'template_name': template.get('name', '')
            }

        except Exception as e:
            logger.error(f"Error generating task: {str(e)}")
            return None

    @staticmethod
    def _validate_template(template: Dict[str, Any]) -> bool:
        """Проверка валидности шаблона"""
        required_fields = ['question_template', 'answer_template']
        for field in required_fields:
            if field not in template or not template[field]:
                logger.error(f"Template missing required field: {field}")
                return False
        return True

    @staticmethod
    def _generate_question(template: str, params: Dict[str, Any]) -> str:
        """Генерация текста вопроса с подстановкой параметров"""
        try:
            question = template
            for param, value in params.items():
                question = question.replace(f'{{{param}}}', str(value))
            return question
        except Exception as e:
            logger.error(f"Error generating question: {str(e)}")
            return ""

    @staticmethod
    def extract_parameters(template_str: str) -> list:
        """Извлечение параметров из шаблона"""
        return list(set(re.findall(r'\{([A-Za-z]+)\}', template_str)))

    @staticmethod
    def generate_from_template(template_id: int) -> Optional[Dict[str, Any]]:
        """Генерация задания по ID шаблона (для API)"""
        # Здесь должна быть логика загрузки шаблона из БД
        # Например:
        # template = db.get_template(template_id)
        # return TaskGenerator.generate_task_variant(template)
        pass