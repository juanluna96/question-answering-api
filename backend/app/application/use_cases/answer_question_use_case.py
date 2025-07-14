import time
from typing import Optional
from ..dto.question_dto import QuestionRequestDTO, AnswerResponseDTO
from ...domain.ports.question_service_port import QuestionServicePort

class AnswerQuestionUseCase:
    """Caso de uso para procesar preguntas y generar respuestas usando RAG"""
    
    def __init__(self, question_service: QuestionServicePort):
        self._question_service = question_service
        self._max_retries = 2  # Número máximo de reintentos en caso de error
    
    async def execute(self, request: QuestionRequestDTO) -> AnswerResponseDTO:
        """
        Ejecuta el caso de uso de responder una pregunta usando el sistema RAG
        
        Args:
            request: DTO con la pregunta a procesar
            
        Returns:
            AnswerResponseDTO: Respuesta procesada con metadatos
            
        Raises:
            ValueError: Si la pregunta no es válida
            Exception: Si hay error en el procesamiento
        """
        start_time = time.time()
        retry_count = 0
        last_error = None
        
        while retry_count <= self._max_retries:
            try:
                # Validar la pregunta usando el servicio
                is_valid = await self._question_service.validate_question(request.question)
                if not is_valid:
                    raise ValueError("La pregunta no es válida para procesamiento RAG")
                
                # Procesar la pregunta con el servicio RAG
                result = await self._question_service.process_question(request.question)
                
                # Calcular tiempo total de procesamiento (incluyendo reintentos)
                total_processing_time = int((time.time() - start_time) * 1000)
                
                # Usar el tiempo del servicio si está disponible, sino el calculado aquí
                service_time = result.get('processing_time_ms', total_processing_time)
                
                # Crear respuesta exitosa
                return AnswerResponseDTO(
                    answer=result['answer'],
                    question=request.question,
                    status="success",
                    confidence=result.get('confidence', 0.8),
                    processing_time_ms=service_time,
                    sources=result.get('source_document_ids'),
                    metadata=result.get('metadata')
                )
                
            except ValueError as e:
                # Error de validación - no reintentar
                processing_time = int((time.time() - start_time) * 1000)
                return AnswerResponseDTO(
                    answer=f"Error de validación: {str(e)}",
                    question=request.question,
                    status="validation_error",
                    confidence=0.0,
                    processing_time_ms=processing_time
                )
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Si no es el último intento, esperar un poco antes del siguiente
                if retry_count <= self._max_retries:
                    await self._wait_before_retry(retry_count)
                    continue
                
                # Si llegamos aquí, se agotaron los reintentos
                break
        
        # Error después de todos los reintentos
        processing_time = int((time.time() - start_time) * 1000)
        error_message = self._get_user_friendly_error_message(last_error) if last_error else "Error desconocido durante el procesamiento"
        
        return AnswerResponseDTO(
            answer=error_message,
            question=request.question,
            status="error",
            confidence=0.0,
            processing_time_ms=processing_time
        )
    
    async def _wait_before_retry(self, retry_count: int) -> None:
        """
        Espera antes de reintentar, con backoff exponencial
        
        Args:
            retry_count: Número del intento actual
        """
        import asyncio
        wait_time = min(2 ** retry_count, 5)  # Máximo 5 segundos
        await asyncio.sleep(wait_time)
    
    def _get_user_friendly_error_message(self, error: Exception) -> str:
        """
        Convierte errores técnicos en mensajes amigables para el usuario
        
        Args:
            error: La excepción original
            
        Returns:
            str: Mensaje de error amigable
        """
        error_str = str(error).lower()
        
        if "timeout" in error_str or "connection" in error_str:
            return "Lo siento, el servicio está experimentando demoras. Por favor, intenta de nuevo en unos momentos."
        elif "rate limit" in error_str or "quota" in error_str:
            return "El servicio está temporalmente sobrecargado. Por favor, intenta de nuevo en unos minutos."
        elif "openai" in error_str or "api" in error_str:
            return "Hay un problema temporal con el servicio de IA. Por favor, intenta de nuevo más tarde."
        elif "embedding" in error_str or "retrieval" in error_str:
            return "No pude encontrar información relevante para tu pregunta. Intenta reformularla."
        else:
            return "Lo siento, ocurrió un error interno al procesar tu pregunta. Por favor, intenta de nuevo."