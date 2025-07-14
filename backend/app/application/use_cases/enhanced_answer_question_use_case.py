import time
from typing import Optional, Dict, Any
from ..dto.question_dto import QuestionRequestDTO, AnswerResponseDTO
from ...domain.ports.question_service_port import QuestionServicePort
from ...infrastructure.services.rag_question_service import RAGQuestionService

class EnhancedAnswerQuestionUseCase:
    """Caso de uso mejorado para procesar preguntas con metadatos completos del RAG"""
    
    def __init__(self, question_service: QuestionServicePort):
        self._question_service = question_service
        self._max_retries = 2
        self._include_debug_info = False  # Para desarrollo/debugging
    
    async def execute(self, 
                     request: QuestionRequestDTO, 
                     include_metadata: bool = False,
                     include_debug: bool = False) -> AnswerResponseDTO:
        """
        Ejecuta el caso de uso de responder una pregunta con metadatos opcionales
        
        Args:
            request: DTO con la pregunta a procesar
            include_metadata: Si incluir metadatos del proceso RAG
            include_debug: Si incluir información de debug (solo desarrollo)
            
        Returns:
            AnswerResponseDTO: Respuesta procesada con metadatos opcionales
        """
        start_time = time.time()
        retry_count = 0
        last_error = None
        debug_info = [] if include_debug else None
        
        if include_debug and debug_info is not None:
            debug_info.append(f"Started processing at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            debug_info.append(f"Question length: {len(request.question)} characters")
        
        while retry_count <= self._max_retries:
            try:
                if include_debug and debug_info is not None:
                    debug_info.append(f"Attempt {retry_count + 1}/{self._max_retries + 1}")
                
                # Validar la pregunta
                is_valid = await self._question_service.validate_question(request.question)
                if not is_valid:
                    raise ValueError("La pregunta no es válida para procesamiento RAG")
                
                if include_debug and debug_info is not None:
                    debug_info.append("Question validation: PASSED")
                
                # Procesar la pregunta
                result = await self._question_service.process_question(request.question)
                
                # Calcular tiempo total
                total_processing_time = int((time.time() - start_time) * 1000)
                service_time = result.get('processing_time_ms', total_processing_time)
                
                if include_debug and debug_info is not None:
                    debug_info.append(f"Processing completed in {service_time}ms")
                    debug_info.append(f"Total time with retries: {total_processing_time}ms")
                
                # Preparar metadatos si se solicitan
                metadata = None
                if include_metadata:
                    metadata = await self._prepare_metadata(
                        result, 
                        request.question, 
                        total_processing_time,
                        retry_count,
                        debug_info
                    )
                
                # Crear respuesta exitosa
                return AnswerResponseDTO(
                    answer=result['answer'],
                    question=request.question,
                    status="success",
                    confidence=result.get('confidence', 0.8),
                    processing_time_ms=service_time,
                    sources=result.get('source_document_ids'),
                    metadata=metadata
                )
                
            except ValueError as e:
                # Error de validación - no reintentar
                if include_debug and debug_info is not None:
                    debug_info.append(f"Validation error: {str(e)}")
                
                processing_time = int((time.time() - start_time) * 1000)
                metadata = self._prepare_error_metadata(
                    e, "validation_error", processing_time, debug_info
                ) if include_metadata else None
                
                return AnswerResponseDTO(
                    answer=f"Error de validación: {str(e)}",
                    question=request.question,
                    status="validation_error",
                    confidence=0.0,
                    processing_time_ms=processing_time,
                    metadata=metadata
                )
                
            except Exception as e:
                last_error = e
                retry_count += 1
                
                if include_debug and debug_info is not None:
                    debug_info.append(f"Error on attempt {retry_count}: {str(e)}")
                
                # Si no es el último intento, esperar antes del siguiente
                if retry_count <= self._max_retries:
                    wait_time = await self._wait_before_retry(retry_count)
                    if include_debug and debug_info is not None:
                        debug_info.append(f"Waiting {wait_time}s before retry")
                    continue
                
                break
        
        # Error después de todos los reintentos
        processing_time = int((time.time() - start_time) * 1000)
        error_message = self._get_user_friendly_error_message(last_error if last_error is not None else Exception("Unknown error"))
        
        if include_debug and debug_info is not None:
            debug_info.append(f"All retries exhausted. Final error: {str(last_error)}")
        
        metadata = self._prepare_error_metadata(
            last_error if last_error is not None else Exception("Unknown error"), "error", processing_time, debug_info, retry_count
        ) if include_metadata else None
        
        return AnswerResponseDTO(
            answer=error_message,
            question=request.question,
            status="error",
            confidence=0.0,
            processing_time_ms=processing_time,
            metadata=metadata
        )
    
    async def _prepare_metadata(self, 
                              result: dict, 
                              question: str, 
                              total_time: int,
                              retry_count: int,
                              debug_info: Optional[list] = None) -> Dict[str, Any]:
        """
        Prepara metadatos completos para la respuesta exitosa
        
        Args:
            result: Resultado del servicio de preguntas
            question: Pregunta original
            total_time: Tiempo total de procesamiento
            retry_count: Número de reintentos realizados
            debug_info: Información de debug opcional
            
        Returns:
            Dict[str, Any]: Metadatos estructurados
        """
        metadata = {
            'processing': {
                'total_time_ms': total_time,
                'service_time_ms': result.get('processing_time_ms'),
                'retry_count': retry_count,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'question_analysis': {
                'length': len(question),
                'word_count': len(question.split()),
                'has_question_marks': '?' in question
            },
            'response_analysis': {
                'answer_length': len(result.get('answer', '')),
                'confidence_score': result.get('confidence'),
                'answer_word_count': len(result.get('answer', '').split())
            }
        }
        
        # Añadir estadísticas del servicio RAG si está disponible
        if isinstance(self._question_service, RAGQuestionService):
            try:
                service_stats = await self._question_service.get_service_statistics()
                metadata['rag_service'] = service_stats
            except Exception:
                metadata['rag_service'] = {'error': 'Could not retrieve RAG statistics'}
        
        # Añadir información de debug si está disponible
        if debug_info:
            metadata['debug'] = {
                'enabled': True,
                'log': debug_info
            }
        
        return metadata
    
    def _prepare_error_metadata(self, 
                              error: Exception, 
                              error_type: str, 
                              processing_time: int,
                              debug_info: Optional[list] = None,
                              retry_count: int = 0) -> Dict[str, Any]:
        """
        Prepara metadatos para respuestas de error
        
        Args:
            error: Excepción que causó el error
            error_type: Tipo de error
            processing_time: Tiempo de procesamiento
            debug_info: Información de debug opcional
            retry_count: Número de reintentos realizados
            
        Returns:
            Dict[str, Any]: Metadatos de error
        """
        metadata = {
            'error': {
                'type': error_type,
                'message': str(error),
                'error_class': error.__class__.__name__,
                'retry_count': retry_count,
                'processing_time_ms': processing_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        if debug_info:
            metadata['debug'] = {
                'enabled': True,
                'log': debug_info
            }
        
        return metadata
    
    async def _wait_before_retry(self, retry_count: int) -> float:
        """
        Espera antes de reintentar con backoff exponencial
        
        Args:
            retry_count: Número del intento actual
            
        Returns:
            float: Tiempo de espera en segundos
        """
        import asyncio
        wait_time = min(2 ** retry_count, 5)  # Máximo 5 segundos
        await asyncio.sleep(wait_time)
        return wait_time
    
    def _get_user_friendly_error_message(self, error: Exception) -> str:
        """
        Convierte errores técnicos en mensajes amigables
        
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
        elif "validation" in error_str:
            return "Tu pregunta no cumple con los criterios de validación. Por favor, reformúlala."
        else:
            return "Lo siento, ocurrió un error interno al procesar tu pregunta. Por favor, intenta de nuevo."
    
    async def get_service_health(self) -> Dict[str, Any]:
        """
        Obtiene información de salud del servicio
        
        Returns:
            Dict[str, Any]: Estado de salud del servicio
        """
        try:
            # Verificar que el servicio puede validar preguntas
            test_validation = await self._question_service.validate_question("test question")
            
            health_info = {
                'status': 'healthy',
                'service_type': self._question_service.__class__.__name__,
                'validation_test': 'passed' if test_validation else 'failed',
                'max_retries': self._max_retries,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Añadir estadísticas específicas del RAG si está disponible
            if isinstance(self._question_service, RAGQuestionService):
                try:
                    service_stats = await self._question_service.get_service_statistics()
                    health_info['rag_statistics'] = service_stats
                except Exception as e:
                    health_info['rag_statistics_error'] = str(e)
            
            return health_info
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'error_type': e.__class__.__name__,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }