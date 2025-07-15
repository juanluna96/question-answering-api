"""Tests para AnswerQuestionUseCase"""

import pytest
import time
from unittest.mock import patch

from app.application.use_cases.answer_question_use_case import AnswerQuestionUseCase
from app.application.dto.question_dto import QuestionRequestDTO, AnswerResponseDTO


class TestAnswerQuestionUseCase:
    """Tests para el caso de uso de responder preguntas"""
    
    @pytest.fixture
    def use_case(self, mock_question_service):
        """Fixture que proporciona una instancia del caso de uso"""
        return AnswerQuestionUseCase(mock_question_service)
    
    @pytest.mark.asyncio
    async def test_execute_successful_response(self, use_case, sample_question_request, mock_question_service):
        """Test de ejecución exitosa con respuesta válida"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_return_value = {
            'answer': 'La inteligencia artificial es una tecnología...',
            'confidence': 0.9,
            'processing_time_ms': 200,
            'source_document_ids': ['doc_1', 'doc_2', 'doc_3'],
            'metadata': {'tokens_used': 150}
        }
        
        # Act
        result = await use_case.execute(sample_question_request)
        
        # Assert
        assert isinstance(result, AnswerResponseDTO)
        assert result.status == "success"
        assert result.answer == 'La inteligencia artificial es una tecnología...'
        assert result.question == sample_question_request.question
        assert result.confidence == 0.9
        assert result.sources == ['doc_1', 'doc_2', 'doc_3']
        assert result.metadata == {'tokens_used': 150}
        assert result.processing_time_ms >= 0
        
        # Verificar que se llamaron los métodos del servicio
        assert mock_question_service.validate_question_call_count == 1
        assert mock_question_service.process_question_call_count == 1
        assert mock_question_service.last_question_validated == sample_question_request.question
        assert mock_question_service.last_question_processed == sample_question_request.question
    
    @pytest.mark.asyncio
    async def test_execute_validation_error(self, use_case, sample_question_request, mock_question_service):
        """Test de error de validación"""
        # Arrange
        mock_question_service.validate_question_return_value = False
        
        # Act
        result = await use_case.execute(sample_question_request)
        
        # Assert
        assert isinstance(result, AnswerResponseDTO)
        assert result.status == "validation_error"
        assert "Error de validación" in result.answer
        assert result.confidence == 0.0
        assert result.sources is None
        assert result.metadata is None
        
        # Verificar que solo se llamó validate_question
        assert mock_question_service.validate_question_call_count == 1
        assert mock_question_service.process_question_call_count == 0
    
    @pytest.mark.asyncio
    async def test_execute_validation_exception(self, use_case, sample_question_request, mock_question_service):
        """Test de excepción durante la validación"""
        # Arrange
        mock_question_service.validate_question_side_effect = ValueError("Pregunta inválida")
        
        # Act
        result = await use_case.execute(sample_question_request)
        
        # Assert
        assert isinstance(result, AnswerResponseDTO)
        assert result.status == "validation_error"
        assert "Error de validación: Pregunta inválida" in result.answer
        assert result.confidence == 0.0
        assert result.sources is None
        assert result.metadata is None
    
    @pytest.mark.asyncio
    async def test_execute_processing_error_with_retries(self, use_case, sample_question_request, mock_question_service):
        """Test de error de procesamiento con reintentos"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_side_effect = Exception("OpenAI API error")
        
        # Mock asyncio.sleep para acelerar el test
        with patch('asyncio.sleep', return_value=None):
            # Act
            result = await use_case.execute(sample_question_request)
        
        # Assert
        assert isinstance(result, AnswerResponseDTO)
        assert result.status == "error"
        assert "problema temporal con el servicio de IA" in result.answer
        assert result.confidence == 0.0
        assert result.sources is None
        assert result.metadata is None
        
        # Verificar que se intentó 3 veces (1 inicial + 2 reintentos)
        assert mock_question_service.process_question_call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_timeout_error_message(self, use_case, sample_question_request, mock_question_service, openai_timeout_error):
        """Test de mensaje de error específico para timeout"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_side_effect = openai_timeout_error
        
        with patch('asyncio.sleep', return_value=None):
            # Act
            result = await use_case.execute(sample_question_request)
        
        # Assert
        assert result.status == "error"
        assert "experimentando demoras" in result.answer
    
    @pytest.mark.asyncio
    async def test_execute_rate_limit_error_message(self, use_case, sample_question_request, mock_question_service, openai_rate_limit_error):
        """Test de mensaje de error específico para rate limit"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_side_effect = openai_rate_limit_error
        
        with patch('asyncio.sleep', return_value=None):
            # Act
            result = await use_case.execute(sample_question_request)
        
        # Assert
        assert result.status == "error"
        assert "temporalmente sobrecargado" in result.answer
    
    @pytest.mark.asyncio
    async def test_execute_embedding_error_message(self, use_case, sample_question_request, mock_question_service, embedding_retrieval_error):
        """Test de mensaje de error específico para problemas de embedding"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_side_effect = embedding_retrieval_error
        
        with patch('asyncio.sleep', return_value=None):
            # Act
            result = await use_case.execute(sample_question_request)
        
        # Assert
        assert result.status == "error"
        assert "información relevante" in result.answer
    
    @pytest.mark.asyncio
    async def test_execute_successful_after_retry(self, use_case, sample_question_request, mock_question_service):
        """Test de éxito después de un reintento"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        
        # Configurar para fallar la primera vez y tener éxito la segunda
        call_count = 0
        def side_effect_function(question):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary error")
            return {
                'answer': 'Respuesta exitosa después del reintento',
                'confidence': 0.8,
                'processing_time_ms': 300,
                'source_document_ids': ['doc_1'],
                'metadata': {}
            }
        
        mock_question_service.process_question_side_effect = side_effect_function
        
        with patch('asyncio.sleep', return_value=None):
            # Act
            result = await use_case.execute(sample_question_request)
        
        # Assert
        assert result.status == "success"
        assert result.answer == 'Respuesta exitosa después del reintento'
        assert call_count == 2  # Falló una vez, exitoso la segunda
    
    @pytest.mark.asyncio
    async def test_execute_processing_time_calculation(self, use_case, sample_question_request, mock_question_service):
        """Test de cálculo correcto del tiempo de procesamiento"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_return_value = {
            'answer': 'Respuesta de prueba',
            'confidence': 0.7,
            'source_document_ids': [],
            'metadata': {}
            # No incluimos processing_time_ms para probar el cálculo interno
        }
        
        # Act
        start_time = time.time()
        result = await use_case.execute(sample_question_request)
        end_time = time.time()
        
        # Assert
        assert result.processing_time_ms >= 0
        # El tiempo debería ser razonable (menos de 1 segundo para un test)
        assert result.processing_time_ms < (end_time - start_time) * 1000 + 100
    
    @pytest.mark.asyncio
    async def test_execute_uses_service_processing_time_when_available(self, use_case, sample_question_request, mock_question_service):
        """Test que usa el tiempo de procesamiento del servicio cuando está disponible"""
        # Arrange
        service_processing_time = 250
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_return_value = {
            'answer': 'Respuesta de prueba',
            'confidence': 0.7,
            'processing_time_ms': service_processing_time,
            'source_document_ids': [],
            'metadata': {}
        }
        
        # Act
        result = await use_case.execute(sample_question_request)
        
        # Assert
        assert result.processing_time_ms == service_processing_time
    
    @pytest.mark.asyncio
    async def test_execute_sources_handling_with_empty_list(self, use_case, sample_question_request, mock_question_service):
        """Test de manejo de sources cuando la lista está vacía"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_return_value = {
            'answer': 'Respuesta sin fuentes',
            'confidence': 0.6,
            'processing_time_ms': 100,
            'source_document_ids': [],  # Lista vacía
            'metadata': {}
        }
        
        # Act
        result = await use_case.execute(sample_question_request)
        
        # Assert
        assert result.sources is None  # Debería ser None, no lista vacía
    
    @pytest.mark.asyncio
    async def test_execute_sources_handling_with_none(self, use_case, sample_question_request, mock_question_service):
        """Test de manejo de sources cuando es None"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_return_value = {
            'answer': 'Respuesta sin fuentes',
            'confidence': 0.6,
            'processing_time_ms': 100,
            'source_document_ids': None,
            'metadata': {}
        }
        
        # Act
        result = await use_case.execute(sample_question_request)
        
        # Assert
        assert result.sources is None
    
    @pytest.mark.asyncio
    async def test_execute_generic_response_detection(self, use_case, sample_question_request, mock_question_service):
        """Test de detección de respuestas genéricas"""
        # Arrange
        mock_question_service.validate_question_return_value = True
        mock_question_service.process_question_return_value = {
            'answer': 'La información proporcionada no contiene detalles específicos sobre este tema.',
            'confidence': 0.3,
            'processing_time_ms': 100,
            'source_document_ids': ['doc_1', 'doc_2'],  # Hay documentos pero respuesta genérica
            'metadata': {}
        }
        
        # Act
        result = await use_case.execute(sample_question_request)
        
        # Assert
        assert result.sources is None  # Debería ser None por respuesta genérica
    
    def test_get_user_friendly_error_message_timeout(self, mock_question_service):
        """Test de mensaje amigable para errores de timeout"""
        # Arrange
        use_case = AnswerQuestionUseCase(mock_question_service)
        error = Exception("Connection timeout occurred")
        
        # Act
        message = use_case._get_user_friendly_error_message(error)
        
        # Assert
        assert "experimentando demoras" in message
    
    def test_get_user_friendly_error_message_rate_limit(self, mock_question_service):
        """Test de mensaje amigable para errores de rate limit"""
        # Arrange
        use_case = AnswerQuestionUseCase(mock_question_service)
        error = Exception("Rate limit exceeded")
        
        # Act
        message = use_case._get_user_friendly_error_message(error)
        
        # Assert
        assert "temporalmente sobrecargado" in message
    
    def test_get_user_friendly_error_message_generic(self, mock_question_service):
        """Test de mensaje amigable para errores genéricos"""
        # Arrange
        use_case = AnswerQuestionUseCase(mock_question_service)
        error = Exception("Some unknown error")
        
        # Act
        message = use_case._get_user_friendly_error_message(error)
        
        # Assert
        assert "error interno" in message
    
    @pytest.mark.asyncio
    async def test_wait_before_retry_timing(self, mock_question_service):
        """Test de timing del backoff exponencial"""
        # Arrange
        use_case = AnswerQuestionUseCase(mock_question_service)
        
        with patch('asyncio.sleep') as mock_sleep:
            # Act
            await use_case._wait_before_retry(1)
            await use_case._wait_before_retry(2)
            await use_case._wait_before_retry(3)
            
            # Assert
            expected_calls = [2, 4, 5]  # 2^1, 2^2, min(2^3, 5)
            actual_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_calls == expected_calls