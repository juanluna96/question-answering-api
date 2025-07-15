"""Tests para EnhancedAnswerQuestionUseCase"""

import pytest
import time
from unittest.mock import patch, AsyncMock

from app.application.use_cases.enhanced_answer_question_use_case import EnhancedAnswerQuestionUseCase
from app.application.dto.question_dto import QuestionRequestDTO, AnswerResponseDTO
from app.infrastructure.services.rag_question_service import RAGQuestionService


class MockRAGQuestionService:
    """Mock específico para RAGQuestionService con estadísticas"""
    
    def __init__(self):
        self.validate_question_return_value = True
        self.process_question_return_value = {
            'answer': 'Esta es una respuesta de prueba mejorada',
            'confidence': 0.85,
            'processing_time_ms': 150,
            'source_document_ids': ['doc_1', 'doc_2'],
            'metadata': {'test': True}
        }
        self.validate_question_side_effect = None
        self.process_question_side_effect = None
        self.service_statistics = {
            'total_questions_processed': 100,
            'average_response_time': 200,
            'cache_hit_rate': 0.75
        }
        
        # Contadores
        self.validate_question_call_count = 0
        self.process_question_call_count = 0
        self.get_service_statistics_call_count = 0
    
    async def validate_question(self, question: str) -> bool:
        self.validate_question_call_count += 1
        if self.validate_question_side_effect:
            raise self.validate_question_side_effect
        return self.validate_question_return_value
    
    async def process_question(self, question: str) -> dict:
        self.process_question_call_count += 1
        if self.process_question_side_effect:
            if callable(self.process_question_side_effect):
                # Si es una función, llamarla con la pregunta
                return self.process_question_side_effect(question)
            else:
                # Si es una excepción, lanzarla
                raise self.process_question_side_effect
        return self.process_question_return_value.copy()
    
    async def get_service_statistics(self) -> dict:
        self.get_service_statistics_call_count += 1
        return self.service_statistics.copy()


class TestEnhancedAnswerQuestionUseCase:
    """Tests para el caso de uso mejorado de responder preguntas"""
    
    @pytest.fixture
    def mock_rag_service(self):
        """Fixture que proporciona un mock del servicio RAG"""
        return MockRAGQuestionService()
    
    @pytest.fixture
    def enhanced_use_case(self, mock_rag_service):
        """Fixture que proporciona una instancia del caso de uso mejorado"""
        return EnhancedAnswerQuestionUseCase(mock_rag_service)
    
    @pytest.mark.asyncio
    async def test_execute_basic_functionality(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de funcionalidad básica sin metadatos ni debug"""
        # Act
        result = await enhanced_use_case.execute(sample_question_request)
        
        # Assert
        assert isinstance(result, AnswerResponseDTO)
        assert result.status == "success"
        assert result.answer == 'Esta es una respuesta de prueba mejorada'
        assert result.confidence == 0.85
        assert result.sources == ['doc_1', 'doc_2']
        assert result.metadata is None  # Sin metadatos por defecto
        
        # Verificar llamadas al servicio
        assert mock_rag_service.validate_question_call_count == 1
        assert mock_rag_service.process_question_call_count == 1
        assert mock_rag_service.get_service_statistics_call_count == 0  # No se llama sin metadatos
    
    @pytest.mark.asyncio
    async def test_execute_with_metadata(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de ejecución con metadatos incluidos"""
        # Act
        result = await enhanced_use_case.execute(
            sample_question_request, 
            include_metadata=True
        )
        
        # Assert
        assert result.metadata is not None
        assert 'processing' in result.metadata
        assert 'question_analysis' in result.metadata
        assert 'response_analysis' in result.metadata
        assert 'rag_service' in result.metadata
        
        # Verificar estructura de metadatos de procesamiento
        processing = result.metadata['processing']
        assert 'total_time_ms' in processing
        assert 'service_time_ms' in processing
        assert 'retry_count' in processing
        assert 'timestamp' in processing
        assert processing['retry_count'] == 0
        
        # Verificar análisis de pregunta
        question_analysis = result.metadata['question_analysis']
        assert question_analysis['length'] == len(sample_question_request.question)
        assert question_analysis['word_count'] == len(sample_question_request.question.split())
        assert question_analysis['has_question_marks'] == ('?' in sample_question_request.question)
        
        # Verificar análisis de respuesta
        response_analysis = result.metadata['response_analysis']
        assert response_analysis['answer_length'] == len(result.answer)
        assert response_analysis['confidence_score'] == 0.85
        assert response_analysis['answer_word_count'] == len(result.answer.split())
        
        # Verificar estadísticas del servicio RAG
        rag_service = result.metadata['rag_service']
        assert rag_service['total_questions_processed'] == 100
        assert rag_service['average_response_time'] == 200
        assert rag_service['cache_hit_rate'] == 0.75
        
        # Verificar que se llamó get_service_statistics
        assert mock_rag_service.get_service_statistics_call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_debug(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de ejecución con información de debug"""
        # Act
        result = await enhanced_use_case.execute(
            sample_question_request, 
            include_metadata=True,
            include_debug=True
        )
        
        # Assert
        assert result.metadata is not None
        assert 'debug' in result.metadata
        
        debug_info = result.metadata['debug']
        assert debug_info['enabled'] is True
        assert 'log' in debug_info
        assert isinstance(debug_info['log'], list)
        assert len(debug_info['log']) > 0
        
        # Verificar que hay entradas de debug esperadas
        debug_log = debug_info['log']
        assert any('Started processing' in entry for entry in debug_log)
        assert any('Question length:' in entry for entry in debug_log)
        assert any('Attempt 1/' in entry for entry in debug_log)
        assert any('Question validation: PASSED' in entry for entry in debug_log)
        assert any('Processing completed' in entry for entry in debug_log)
    
    @pytest.mark.asyncio
    async def test_execute_validation_error_with_metadata(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de error de validación con metadatos"""
        # Arrange
        mock_rag_service.validate_question_return_value = False
        
        # Act
        result = await enhanced_use_case.execute(
            sample_question_request,
            include_metadata=True,
            include_debug=True
        )
        
        # Assert
        assert result.status == "validation_error"
        assert result.metadata is not None
        assert 'error_type' in result.metadata
        assert 'error_message' in result.metadata
        assert 'processing_time_ms' in result.metadata
        assert result.metadata['error_type'] == 'validation_error'
        
        # Verificar debug info para error
        assert 'debug' in result.metadata
        debug_log = result.metadata['debug']['log']
        assert any('Validation error:' in entry for entry in debug_log)
    
    @pytest.mark.asyncio
    async def test_execute_processing_error_with_retries_and_debug(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de error de procesamiento con reintentos y debug"""
        # Arrange
        mock_rag_service.validate_question_return_value = True
        mock_rag_service.process_question_side_effect = Exception("Processing failed")
        
        with patch('asyncio.sleep', return_value=None):
            # Act
            result = await enhanced_use_case.execute(
                sample_question_request,
                include_metadata=True,
                include_debug=True
            )
        
        # Assert
        assert result.status == "error"
        assert result.metadata is not None
        assert result.metadata['error_type'] == 'error'
        assert 'retry_count' in result.metadata
        assert result.metadata['retry_count'] == 2  # Máximo de reintentos
        
        # Verificar debug info para reintentos
        debug_log = result.metadata['debug']['log']
        assert any('Error on attempt' in entry for entry in debug_log)
        assert any('Waiting' in entry and 'before retry' in entry for entry in debug_log)
        assert any('All retries exhausted' in entry for entry in debug_log)
        
        # Verificar que se intentó el número correcto de veces
        assert mock_rag_service.process_question_call_count == 3  # 1 inicial + 2 reintentos
    
    @pytest.mark.asyncio
    async def test_execute_successful_after_retry_with_debug(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de éxito después de reintento con debug"""
        # Arrange
        mock_rag_service.validate_question_return_value = True
        
        call_count = 0
        def side_effect_function(question):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary error")
            return {
                'answer': 'Éxito después del reintento',
                'confidence': 0.8,
                'processing_time_ms': 300,
                'source_document_ids': ['doc_1'],
                'metadata': {}
            }
        
        mock_rag_service.process_question_side_effect = side_effect_function
        
        with patch('asyncio.sleep', return_value=None):
            # Act
            result = await enhanced_use_case.execute(
                sample_question_request,
                include_metadata=True,
                include_debug=True
            )
        
        # Assert
        assert result.status == "success"
        assert result.answer == 'Éxito después del reintento'
        assert result.metadata is not None
        assert result.metadata['processing']['retry_count'] == 1
        
        # Verificar debug info
        debug_log = result.metadata['debug']['log']
        assert any('Error on attempt 1:' in entry for entry in debug_log)
        assert any('Attempt 2/' in entry for entry in debug_log)
    
    @pytest.mark.asyncio
    async def test_rag_service_statistics_error_handling(self, enhanced_use_case, sample_question_request):
        """Test de manejo de errores al obtener estadísticas del servicio RAG"""
        # Arrange
        mock_service = MockRAGQuestionService()
        
        # Simular error al obtener estadísticas
        async def failing_get_statistics():
            raise Exception("Statistics service unavailable")
        
        mock_service.get_service_statistics = failing_get_statistics
        enhanced_use_case._question_service = mock_service
        
        # Act
        result = await enhanced_use_case.execute(
            sample_question_request,
            include_metadata=True
        )
        
        # Assert
        assert result.status == "success"
        assert result.metadata is not None
        assert 'rag_service' in result.metadata
        assert 'error' in result.metadata['rag_service']
        assert result.metadata['rag_service']['error'] == 'Could not retrieve RAG statistics'
    
    @pytest.mark.asyncio
    async def test_non_rag_service_metadata(self, sample_question_request, mock_question_service):
        """Test de metadatos cuando no se usa RAGQuestionService"""
        # Arrange - usar el mock básico que no es RAGQuestionService
        enhanced_use_case = EnhancedAnswerQuestionUseCase(mock_question_service)
        
        # Act
        result = await enhanced_use_case.execute(
            sample_question_request,
            include_metadata=True
        )
        
        # Assert
        assert result.status == "success"
        assert result.metadata is not None
        assert 'rag_service' not in result.metadata  # No debería estar presente
        assert 'processing' in result.metadata
        assert 'question_analysis' in result.metadata
        assert 'response_analysis' in result.metadata
    
    @pytest.mark.asyncio
    async def test_metadata_timing_accuracy(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de precisión en los tiempos de metadatos"""
        # Arrange
        mock_rag_service.process_question_return_value['processing_time_ms'] = 250
        
        # Act
        start_time = time.time()
        result = await enhanced_use_case.execute(
            sample_question_request,
            include_metadata=True
        )
        end_time = time.time()
        
        # Assert
        assert result.metadata is not None
        processing_metadata = result.metadata['processing']
        assert processing_metadata['service_time_ms'] == 250
        assert processing_metadata['total_time_ms'] >= 0
        # El tiempo total debería ser razonable
        expected_max_time = (end_time - start_time) * 1000 + 100
        assert processing_metadata['total_time_ms'] < expected_max_time
    
    @pytest.mark.asyncio
    async def test_debug_disabled_by_default(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test que debug está deshabilitado por defecto"""
        # Act
        result = await enhanced_use_case.execute(
            sample_question_request,
            include_metadata=True
            # include_debug=False por defecto
        )
        
        # Assert
        assert result.metadata is not None
        assert 'debug' not in result.metadata
    
    @pytest.mark.asyncio
    async def test_sources_conditional_logic_generic_response(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de lógica condicional de sources con respuesta genérica"""
        # Arrange
        mock_rag_service.process_question_return_value = {
            'answer': 'La información proporcionada no contiene detalles específicos.',
            'confidence': 0.3,
            'processing_time_ms': 100,
            'source_document_ids': ['doc_1', 'doc_2'],  # Hay documentos pero respuesta genérica
            'metadata': {}
        }
        
        # Act
        result = await enhanced_use_case.execute(sample_question_request)
        
        # Assert
        assert result.sources is None  # Debería ser None por respuesta genérica
    
    @pytest.mark.asyncio
    async def test_sources_conditional_logic_empty_sources(self, enhanced_use_case, sample_question_request, mock_rag_service):
        """Test de lógica condicional de sources con lista vacía"""
        # Arrange
        mock_rag_service.process_question_return_value = {
            'answer': 'Respuesta específica basada en documentos',
            'confidence': 0.8,
            'processing_time_ms': 100,
            'source_document_ids': [],  # Lista vacía
            'metadata': {}
        }
        
        # Act
        result = await enhanced_use_case.execute(sample_question_request)
        
        # Assert
        assert result.sources is None  # Debería ser None por lista vacía
    
    @pytest.mark.asyncio
    async def test_wait_before_retry_returns_wait_time(self, enhanced_use_case):
        """Test que _wait_before_retry retorna el tiempo de espera"""
        with patch('asyncio.sleep', return_value=None) as mock_sleep:
            # Act
            wait_time = await enhanced_use_case._wait_before_retry(1)
            
            # Assert
            assert wait_time == 2  # 2^1
            mock_sleep.assert_called_once_with(2)
            
            # Test con retry_count mayor
            wait_time = await enhanced_use_case._wait_before_retry(3)
            assert wait_time == 5  # min(2^3, 5) = min(8, 5) = 5