import time
from typing import Optional, List
from ...domain.ports.question_service_port import QuestionServicePort
from ...domain.entities.document import Document
from .rag_generation_service import RAGGenerationService
from .rag_retrieval_service import RAGRetrievalService

class RAGQuestionService(QuestionServicePort):
    """Implementación del servicio de procesamiento de preguntas usando RAG"""
    
    def __init__(self, 
                 generation_service: RAGGenerationService,
                 retrieval_service: RAGRetrievalService):
        """
        Inicializa el servicio RAG de preguntas
        
        Args:
            generation_service: Servicio de generación RAG
            retrieval_service: Servicio de recuperación de documentos
        """
        self._generation_service = generation_service
        self._retrieval_service = retrieval_service
        
        # Configuración de validación
        self._min_question_length = 3
        self._max_question_length = 1000
        self._prohibited_words = {
            'spam', 'test', 'prueba123', 'asdfgh', 'qwerty',
            'admin', 'password', 'hack', 'exploit'
        }
    
    async def process_question(self, question: str) -> dict:
        """
        Procesa una pregunta usando el sistema RAG completo
        
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
        start_time = time.time()
        
        try:
            # 1. Recuperar documentos relevantes
            search_results = await self._retrieval_service.search_documents(
                query=question,
                top_k=5  # Recuperar top 5 documentos más relevantes
            )
            
            # Extraer documentos de los resultados de búsqueda
            retrieved_documents = []
            for result in search_results:
                doc_embedding = result[0]  # DocumentEmbedding
                # Crear Document a partir de DocumentEmbedding
                document = Document(
                    id=doc_embedding.document_id,
                    content=doc_embedding.content
                )
                retrieved_documents.append(document)
            
            # 2. Generar respuesta usando RAG
            rag_response = await self._generation_service.generate_answer(
                question=question,
                retrieved_documents=retrieved_documents,
                include_metadata=True
            )
            
            # 3. Calcular tiempo total de procesamiento
            total_processing_time = int((time.time() - start_time) * 1000)
            
            # 4. Extraer información de la respuesta RAG
            if rag_response.get('status') == 'success':
                # Calcular confianza basada en múltiples factores
                confidence = self._calculate_confidence(
                    rag_response=rag_response,
                    question=question,
                    num_documents=len(retrieved_documents)
                )
                
                return {
                    'answer': rag_response['answer'],
                    'confidence': confidence,
                    'processing_time_ms': total_processing_time
                }
            else:
                # Error en la generación RAG
                return {
                    'answer': rag_response.get('answer', 'Lo siento, no pude procesar tu pregunta.'),
                    'confidence': 0.0,
                    'processing_time_ms': total_processing_time
                }
                
        except Exception as e:
            # Error inesperado
            processing_time = int((time.time() - start_time) * 1000)
            return {
                'answer': f'Lo siento, ocurrió un error al procesar tu pregunta: {str(e)}',
                'confidence': 0.0,
                'processing_time_ms': processing_time
            }
    
    async def validate_question(self, question: str) -> bool:
        """
        Valida si una pregunta es procesable por el sistema RAG
        
        Args:
            question: La pregunta a validar
            
        Returns:
            bool: True si la pregunta es válida, False en caso contrario
        """
        if not question or not isinstance(question, str):
            return False
        
        # Limpiar la pregunta
        cleaned_question = question.strip()
        
        # Verificar longitud
        if len(cleaned_question) < self._min_question_length:
            return False
        
        if len(cleaned_question) > self._max_question_length:
            return False
        
        # Verificar que contenga al menos un carácter alfanumérico
        if not any(c.isalnum() for c in cleaned_question):
            return False
        
        # Verificar que no sea solo números
        if cleaned_question.isdigit():
            return False
        
        # Verificar palabras prohibidas
        question_lower = cleaned_question.lower()
        if any(prohibited_word in question_lower for prohibited_word in self._prohibited_words):
            return False
        
        # Verificar que no sea solo caracteres repetidos
        if len(set(cleaned_question.replace(' ', ''))) < 3:
            return False
        
        # Verificar que tenga al menos una palabra real (más de 2 caracteres)
        words = cleaned_question.split()
        if not any(len(word) > 2 for word in words):
            return False
        
        return True
    
    def _calculate_confidence(self, 
                            rag_response: dict, 
                            question: str, 
                            num_documents: int) -> float:
        """
        Calcula el nivel de confianza de la respuesta basado en múltiples factores
        
        Args:
            rag_response: Respuesta del sistema RAG
            question: Pregunta original
            num_documents: Número de documentos recuperados
            
        Returns:
            float: Nivel de confianza entre 0.0 y 1.0
        """
        base_confidence = 0.7  # Confianza base
        
        # Factor 1: Calidad de la respuesta (longitud y estructura)
        answer = rag_response.get('answer', '')
        if len(answer) > 50:  # Respuesta sustancial
            base_confidence += 0.1
        if len(answer) > 200:  # Respuesta detallada
            base_confidence += 0.1
        
        # Factor 2: Número de documentos recuperados
        if num_documents >= 3:
            base_confidence += 0.05
        if num_documents >= 5:
            base_confidence += 0.05
        
        # Factor 3: Metadatos del RAG (si están disponibles)
        metadata = rag_response.get('metadata', {})
        rag_stats = metadata.get('rag_service', {})
        
        # Si hay estadísticas de contexto, usar para ajustar confianza
        if 'context_stats' in rag_stats:
            context_stats = rag_stats['context_stats']
            if context_stats.get('total_documents', 0) > 0:
                base_confidence += 0.05
        
        # Factor 4: Longitud y complejidad de la pregunta
        question_words = len(question.split())
        if question_words >= 5:  # Pregunta bien formulada
            base_confidence += 0.05
        
        # Asegurar que la confianza esté en el rango [0.0, 1.0]
        return min(1.0, max(0.0, round(base_confidence, 2)))
    
    async def get_service_statistics(self) -> dict:
        """
        Obtiene estadísticas de los servicios RAG
        
        Returns:
            dict: Estadísticas de generación y recuperación
        """
        try:
            generation_stats = self._generation_service.get_rag_statistics()
            # Note: Asumiendo que el retrieval service también tiene estadísticas
            # Si no las tiene, se puede omitir o implementar
            
            return {
                'generation_service': generation_stats,
                'service_type': 'RAG Question Service',
                'status': 'active'
            }
        except Exception as e:
            return {
                'error': f'Error obteniendo estadísticas: {str(e)}',
                'service_type': 'RAG Question Service',
                'status': 'error'
            }
    
    async def reset_service_statistics(self) -> bool:
        """
        Reinicia las estadísticas de los servicios RAG
        
        Returns:
            bool: True si se reiniciaron correctamente
        """
        try:
            self._generation_service.reset_statistics()
            return True
        except Exception:
            return False