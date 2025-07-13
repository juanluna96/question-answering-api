import asyncio
import random
from typing import Optional
from ...domain.ports.question_service_port import QuestionServicePort

class SimpleQuestionService(QuestionServicePort):
    """Implementación simple del servicio de procesamiento de preguntas"""
    
    def __init__(self):
        # Respuestas predefinidas para demostración
        self._sample_responses = [
            "Esa es una excelente pregunta. Basándome en la información disponible, puedo decirte que...",
            "Según mi análisis, la respuesta más probable es...",
            "Es interesante que preguntes sobre eso. La respuesta depende de varios factores...",
            "Permíteme explicarte esto de manera clara...",
            "Basándome en los datos que tengo, puedo concluir que..."
        ]
    
    async def process_question(self, question: str) -> dict:
        """
        Procesa una pregunta y retorna una respuesta simulada
        
        Args:
            question: La pregunta a procesar
            
        Returns:
            dict: Diccionario con la respuesta, confianza y tiempo de procesamiento
        """
        # Simular tiempo de procesamiento
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Generar respuesta basada en la pregunta
        response_template = random.choice(self._sample_responses)
        
        # Personalizar respuesta según el tipo de pregunta
        if "qué" in question.lower() or "que" in question.lower():
            answer = f"{response_template} La respuesta a '{question}' requiere considerar múltiples aspectos."
        elif "cómo" in question.lower() or "como" in question.lower():
            answer = f"{response_template} Para '{question}', te recomiendo seguir estos pasos..."
        elif "por qué" in question.lower() or "porque" in question.lower():
            answer = f"{response_template} La razón detrás de '{question}' se debe a varios factores..."
        elif "cuándo" in question.lower() or "cuando" in question.lower():
            answer = f"{response_template} En cuanto a '{question}', el momento depende de las circunstancias..."
        elif "dónde" in question.lower() or "donde" in question.lower():
            answer = f"{response_template} Respecto a '{question}', la ubicación es un factor clave..."
        else:
            answer = f"{response_template} Tu pregunta '{question}' es muy interesante y merece una respuesta detallada."
        
        # Calcular confianza basada en la longitud y complejidad de la pregunta
        confidence = min(0.95, max(0.6, len(question) / 100))
        
        return {
            'answer': answer,
            'confidence': round(confidence, 2),
            'processing_time_ms': random.randint(100, 300)
        }
    
    async def validate_question(self, question: str) -> bool:
        """
        Valida si una pregunta es procesable
        
        Args:
            question: La pregunta a validar
            
        Returns:
            bool: True si la pregunta es válida, False en caso contrario
        """
        if not question or not question.strip():
            return False
        
        # Verificar longitud mínima
        if len(question.strip()) < 3:
            return False
        
        # Verificar que contenga al menos un carácter alfanumérico
        if not any(c.isalnum() for c in question):
            return False
        
        # Verificar que no sea solo números o caracteres especiales
        if question.strip().isdigit():
            return False
        
        # Lista de palabras prohibidas o spam
        prohibited_words = ['spam', 'test', 'prueba123', 'asdfgh']
        if any(word in question.lower() for word in prohibited_words):
            return False
        
        return True