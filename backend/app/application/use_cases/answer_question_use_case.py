import time
from typing import Optional
from ..dto.question_dto import QuestionRequestDTO, AnswerResponseDTO
from ...domain.ports.question_service_port import QuestionServicePort

class AnswerQuestionUseCase:
    """Caso de uso para procesar preguntas y generar respuestas"""
    
    def __init__(self, question_service: QuestionServicePort):
        self._question_service = question_service
    
    async def execute(self, request: QuestionRequestDTO) -> AnswerResponseDTO:
        """
        Ejecuta el caso de uso de responder una pregunta
        
        Args:
            request: DTO con la pregunta a procesar
            
        Returns:
            AnswerResponseDTO: Respuesta procesada
            
        Raises:
            ValueError: Si la pregunta no es válida
            Exception: Si hay error en el procesamiento
        """
        start_time = time.time()
        
        try:
            # Validar la pregunta usando el servicio
            is_valid = await self._question_service.validate_question(request.question)
            if not is_valid:
                raise ValueError("La pregunta no es válida para procesamiento")
            
            # Procesar la pregunta
            result = await self._question_service.process_question(request.question)
            
            # Calcular tiempo de procesamiento
            processing_time = int((time.time() - start_time) * 1000)
            
            # Crear respuesta
            return AnswerResponseDTO(
                answer=result['answer'],
                question=request.question,
                status="success",
                confidence=result.get('confidence'),
                processing_time_ms=processing_time
            )
            
        except ValueError as e:
            # Error de validación
            processing_time = int((time.time() - start_time) * 1000)
            return AnswerResponseDTO(
                answer=f"Error: {str(e)}",
                question=request.question,
                status="error",
                confidence=0.0,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            # Error interno
            processing_time = int((time.time() - start_time) * 1000)
            return AnswerResponseDTO(
                answer="Lo siento, ocurrió un error interno al procesar tu pregunta.",
                question=request.question,
                status="error",
                confidence=0.0,
                processing_time_ms=processing_time
            )