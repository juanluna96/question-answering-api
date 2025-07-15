"""Configuración y fixtures comunes para los tests"""

import pytest
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any, Optional

from app.domain.ports.question_service_port import QuestionServicePort
from app.application.dto.question_dto import QuestionRequestDTO, AnswerResponseDTO


class MockQuestionService(QuestionServicePort):
    """Mock del servicio de preguntas para testing"""
    
    def __init__(self):
        self.validate_question_return_value = True
        self.process_question_return_value = {
            'answer': 'Esta es una respuesta de prueba',
            'confidence': 0.85,
            'processing_time_ms': 150,
            'source_document_ids': ['doc_1', 'doc_2'],
            'metadata': {'test': True}
        }
        self.validate_question_side_effect = None
        self.process_question_side_effect = None
        
        # Contadores para verificar llamadas
        self.validate_question_call_count = 0
        self.process_question_call_count = 0
        self.last_question_validated = None
        self.last_question_processed = None
    
    async def validate_question(self, question: str) -> bool:
        """Mock de validación de pregunta"""
        self.validate_question_call_count += 1
        self.last_question_validated = question
        
        if self.validate_question_side_effect:
            raise self.validate_question_side_effect
            
        return self.validate_question_return_value
    
    async def process_question(self, question: str) -> dict:
        """Mock de procesamiento de pregunta"""
        self.process_question_call_count += 1
        self.last_question_processed = question
        
        if self.process_question_side_effect:
            if callable(self.process_question_side_effect):
                # Si es una función, llamarla con la pregunta
                return self.process_question_side_effect(question)
            else:
                # Si es una excepción, lanzarla
                raise self.process_question_side_effect
            
        return self.process_question_return_value.copy()
    
    async def get_service_statistics(self) -> dict:
        """Mock de estadísticas del servicio"""
        return {
            'service_type': 'Mock Question Service',
            'status': 'active',
            'calls': {
                'validate_question': self.validate_question_call_count,
                'process_question': self.process_question_call_count
            }
        }
    
    def reset_counters(self):
        """Resetea los contadores de llamadas"""
        self.validate_question_call_count = 0
        self.process_question_call_count = 0
        self.last_question_validated = None
        self.last_question_processed = None


@pytest.fixture
def mock_question_service():
    """Fixture que proporciona un mock del servicio de preguntas"""
    return MockQuestionService()


@pytest.fixture
def sample_question_request():
    """Fixture que proporciona una pregunta de ejemplo"""
    return QuestionRequestDTO(question="¿Qué es la inteligencia artificial?")


@pytest.fixture
def sample_invalid_question_request():
    """Fixture que proporciona una pregunta inválida"""
    return QuestionRequestDTO(question="")


@pytest.fixture
def sample_short_question_request():
    """Fixture que proporciona una pregunta muy corta"""
    return QuestionRequestDTO(question="AI")


@pytest.fixture
def expected_success_response():
    """Fixture que proporciona una respuesta exitosa esperada"""
    return {
        'answer': 'Esta es una respuesta de prueba',
        'question': '¿Qué es la inteligencia artificial?',
        'status': 'success',
        'confidence': 0.85,
        'sources': ['doc_1', 'doc_2'],
        'metadata': {'test': True}
    }


@pytest.fixture
def expected_validation_error_response():
    """Fixture que proporciona una respuesta de error de validación esperada"""
    return {
        'status': 'validation_error',
        'confidence': 0.0,
        'sources': None,
        'metadata': None
    }


@pytest.fixture
def expected_processing_error_response():
    """Fixture que proporciona una respuesta de error de procesamiento esperada"""
    return {
        'status': 'error',
        'confidence': 0.0,
        'sources': None,
        'metadata': None
    }


# Fixtures para simular diferentes escenarios de OpenAI
@pytest.fixture
def openai_timeout_error():
    """Simula un error de timeout de OpenAI"""
    return Exception("Request timeout - OpenAI API")


@pytest.fixture
def openai_rate_limit_error():
    """Simula un error de rate limit de OpenAI"""
    return Exception("Rate limit exceeded - OpenAI API")


@pytest.fixture
def openai_quota_error():
    """Simula un error de quota de OpenAI"""
    return Exception("Quota exceeded - OpenAI API")


@pytest.fixture
def generic_api_error():
    """Simula un error genérico de API"""
    return Exception("API connection failed")


@pytest.fixture
def embedding_retrieval_error():
    """Simula un error en la recuperación de embeddings"""
    return Exception("Embedding retrieval failed")