from abc import ABC, abstractmethod
from typing import Optional

class QuestionServicePort(ABC):
    """Puerto para servicios de procesamiento de preguntas"""
    
    @abstractmethod
    async def process_question(self, question: str) -> dict:
        """
        Procesa una pregunta y retorna una respuesta
        
        Args:
            question: La pregunta a procesar
            
        Returns:
            dict: Diccionario con la respuesta, confianza y tiempo de procesamiento
                {
                    'answer': str,
                    'confidence': Optional[float],
                    'processing_time_ms': Optional[int]
                }
        """
        pass
    
    @abstractmethod
    async def validate_question(self, question: str) -> bool:
        """
        Valida si una pregunta es procesable
        
        Args:
            question: La pregunta a validar
            
        Returns:
            bool: True si la pregunta es válida, False en caso contrario
        """
        pass