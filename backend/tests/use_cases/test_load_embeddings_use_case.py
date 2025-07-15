"""Tests para LoadEmbeddingsUseCase y GetCacheStatusUseCase"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from app.application.use_cases.load_embeddings import LoadEmbeddingsUseCase, GetCacheStatusUseCase
from app.application.dto.embedding_dto import EmbeddingResponseDTO, CacheStatusDTO


class MockEmbeddingService:
    """Mock del servicio de embeddings"""
    
    def __init__(self):
        self.model_info = {
            'model_name': 'text-embedding-ada-002',
            'dimensions': 1536,
            'max_tokens': 8191
        }
    
    def get_model_info(self):
        return self.model_info.copy()


class MockCacheService:
    """Mock del servicio de caché"""
    
    def __init__(self):
        self.cache_exists_return_value = True
        self.cache_info = {
            'exists': True,
            'file_path': '/path/to/cache.pkl',
            'size_bytes': 1024000,
            'size_mb': 1.0,
            'embeddings_count': 100,
            'last_modified': datetime.now().timestamp()
        }
    
    async def cache_exists(self):
        return self.cache_exists_return_value
    
    async def get_cache_info(self):
        return self.cache_info.copy()


class MockEmbeddingManager:
    """Mock del manager de embeddings"""
    
    def __init__(self):
        self.embedding_service = MockEmbeddingService()
        self.cache_service = MockCacheService()
        self.embeddings_data = [
            {'id': 'doc_1', 'embedding': [0.1, 0.2, 0.3]},
            {'id': 'doc_2', 'embedding': [0.4, 0.5, 0.6]},
            {'id': 'doc_3', 'embedding': [0.7, 0.8, 0.9]}
        ]
        self.load_or_generate_embeddings_side_effect = None
    
    async def load_or_generate_embeddings(self, csv_path: str, force_regenerate: bool = False):
        if self.load_or_generate_embeddings_side_effect:
            raise self.load_or_generate_embeddings_side_effect
        return self.embeddings_data.copy()


class MockDependencyContainer:
    """Mock del contenedor de dependencias"""
    
    def __init__(self):
        self.embedding_manager = MockEmbeddingManager()
        self.cache_service = MockCacheService()
    
    def get_embedding_manager(self, cache_file_path=None):
        return self.embedding_manager
    
    def get_cache_service(self, cache_file_path=None):
        return self.cache_service


class TestLoadEmbeddingsUseCase:
    """Tests para el caso de uso de carga de embeddings"""
    
    @pytest.fixture
    def mock_dependency_container(self):
        """Fixture que proporciona un mock del contenedor de dependencias"""
        return MockDependencyContainer()
    
    @pytest.fixture
    def load_embeddings_use_case(self, mock_dependency_container):
        """Fixture que proporciona una instancia del caso de uso"""
        return LoadEmbeddingsUseCase(mock_dependency_container)
    
    @pytest.mark.asyncio
    async def test_execute_successful_load_with_cache(self, load_embeddings_use_case, mock_dependency_container):
        """Test de carga exitosa de embeddings usando caché"""
        # Arrange
        csv_file_path = "/path/to/data.csv"
        cache_file_path = "/path/to/cache.pkl"
        
        # Configurar que el caché existe
        mock_dependency_container.embedding_manager.cache_service.cache_exists_return_value = True
        
        # Act
        result = await load_embeddings_use_case.execute(
            csv_file_path=csv_file_path,
            cache_file_path=cache_file_path,
            force_regenerate=False
        )
        
        # Assert
        assert isinstance(result, EmbeddingResponseDTO)
        assert result.success is True
        assert csv_file_path in result.message
        assert result.embeddings_count == 3
        assert result.cache_used is True
        assert result.model_info['model_name'] == 'text-embedding-ada-002'
        assert result.model_info['dimensions'] == 1536
    
    @pytest.mark.asyncio
    async def test_execute_successful_load_without_cache(self, load_embeddings_use_case, mock_dependency_container):
        """Test de carga exitosa de embeddings sin caché"""
        # Arrange
        csv_file_path = "/path/to/data.csv"
        
        # Configurar que el caché no existe
        mock_dependency_container.embedding_manager.cache_service.cache_exists_return_value = False
        
        # Act
        result = await load_embeddings_use_case.execute(
            csv_file_path=csv_file_path,
            force_regenerate=False
        )
        
        # Assert
        assert result.success is True
        assert result.embeddings_count == 3
        assert result.cache_used is False
        assert result.model_info is not None
    
    @pytest.mark.asyncio
    async def test_execute_force_regenerate(self, load_embeddings_use_case, mock_dependency_container):
        """Test de regeneración forzada de embeddings"""
        # Arrange
        csv_file_path = "/path/to/data.csv"
        
        # Configurar que el caché existe pero se fuerza regeneración
        mock_dependency_container.embedding_manager.cache_service.cache_exists_return_value = True
        
        # Act
        result = await load_embeddings_use_case.execute(
            csv_file_path=csv_file_path,
            force_regenerate=True
        )
        
        # Assert
        assert result.success is True
        assert result.embeddings_count == 3
        assert result.cache_used is False  # No usa caché por force_regenerate=True
    
    @pytest.mark.asyncio
    async def test_execute_with_custom_cache_path(self, load_embeddings_use_case, mock_dependency_container):
        """Test de ejecución con ruta de caché personalizada"""
        # Arrange
        csv_file_path = "/path/to/data.csv"
        custom_cache_path = "/custom/cache/path.pkl"
        
        # Mock para verificar que se llama con la ruta correcta
        get_embedding_manager_mock = Mock(return_value=mock_dependency_container.embedding_manager)
        mock_dependency_container.get_embedding_manager = get_embedding_manager_mock
        
        # Act
        result = await load_embeddings_use_case.execute(
            csv_file_path=csv_file_path,
            cache_file_path=custom_cache_path
        )
        
        # Assert
        assert result.success is True
        get_embedding_manager_mock.assert_called_once_with(custom_cache_path)
    
    @pytest.mark.asyncio
    async def test_execute_embedding_manager_error(self, load_embeddings_use_case, mock_dependency_container):
        """Test de manejo de errores del embedding manager"""
        # Arrange
        csv_file_path = "/path/to/data.csv"
        error_message = "Failed to load embeddings"
        
        mock_dependency_container.embedding_manager.load_or_generate_embeddings_side_effect = Exception(error_message)
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await load_embeddings_use_case.execute(csv_file_path=csv_file_path)
        
        assert str(exc_info.value) == error_message
    
    @pytest.mark.asyncio
    async def test_execute_empty_embeddings_result(self, load_embeddings_use_case, mock_dependency_container):
        """Test de resultado con embeddings vacíos"""
        # Arrange
        csv_file_path = "/path/to/empty_data.csv"
        
        # Configurar para retornar lista vacía
        mock_dependency_container.embedding_manager.embeddings_data = []
        
        # Act
        result = await load_embeddings_use_case.execute(csv_file_path=csv_file_path)
        
        # Assert
        assert result.success is True
        assert result.embeddings_count == 0
        assert "exitosamente" in result.message


class TestGetCacheStatusUseCase:
    """Tests para el caso de uso de estado del caché"""
    
    @pytest.fixture
    def mock_dependency_container(self):
        """Fixture que proporciona un mock del contenedor de dependencias"""
        return MockDependencyContainer()
    
    @pytest.fixture
    def cache_status_use_case(self, mock_dependency_container):
        """Fixture que proporciona una instancia del caso de uso"""
        return GetCacheStatusUseCase(mock_dependency_container)
    
    @pytest.mark.asyncio
    async def test_execute_cache_exists(self, cache_status_use_case, mock_dependency_container):
        """Test de estado cuando el caché existe"""
        # Arrange
        cache_file_path = "/path/to/cache.pkl"
        expected_timestamp = datetime.now().timestamp()
        
        mock_dependency_container.cache_service.cache_info = {
            'exists': True,
            'file_path': cache_file_path,
            'size_bytes': 2048000,
            'size_mb': 2.0,
            'embeddings_count': 200,
            'last_modified': expected_timestamp
        }
        
        # Act
        result = await cache_status_use_case.execute(cache_file_path=cache_file_path)
        
        # Assert
        assert isinstance(result, CacheStatusDTO)
        assert result.exists is True
        assert result.file_path == cache_file_path
        assert result.size_bytes == 2048000
        assert result.size_mb == 2.0
        assert result.embeddings_count == 200
        assert result.last_modified == expected_timestamp
    
    @pytest.mark.asyncio
    async def test_execute_cache_does_not_exist(self, cache_status_use_case, mock_dependency_container):
        """Test de estado cuando el caché no existe"""
        # Arrange
        cache_file_path = "/path/to/nonexistent_cache.pkl"
        
        mock_dependency_container.cache_service.cache_info = {
            'exists': False,
            'file_path': cache_file_path,
            'size_bytes': 0,
            'size_mb': 0.0,
            'embeddings_count': 0,
            'last_modified': None
        }
        
        # Act
        result = await cache_status_use_case.execute(cache_file_path=cache_file_path)
        
        # Assert
        assert result.exists is False
        assert result.file_path == cache_file_path
        assert result.size_bytes == 0
        assert result.size_mb == 0.0
        assert result.embeddings_count == 0
        assert result.last_modified is None
    
    @pytest.mark.asyncio
    async def test_execute_without_cache_path(self, cache_status_use_case, mock_dependency_container):
        """Test de estado sin especificar ruta de caché"""
        # Arrange
        mock_dependency_container.cache_service.cache_info = {
            'exists': False,
            'file_path': None,
            'size_bytes': 0,
            'size_mb': 0.0,
            'embeddings_count': 0,
            'last_modified': None
        }
        
        # Act
        result = await cache_status_use_case.execute()
        
        # Assert
        assert result.exists is False
        assert result.file_path is None
        assert result.size_bytes == 0
        assert result.embeddings_count == 0
    
    @pytest.mark.asyncio
    async def test_execute_with_custom_cache_path(self, cache_status_use_case, mock_dependency_container):
        """Test de ejecución con ruta de caché personalizada"""
        # Arrange
        custom_cache_path = "/custom/cache/status.pkl"
        
        # Mock para verificar que se llama con la ruta correcta
        get_cache_service_mock = Mock(return_value=mock_dependency_container.cache_service)
        mock_dependency_container.get_cache_service = get_cache_service_mock
        
        # Act
        result = await cache_status_use_case.execute(cache_file_path=custom_cache_path)
        
        # Assert
        assert isinstance(result, CacheStatusDTO)
        get_cache_service_mock.assert_called_once_with(custom_cache_path)
    
    @pytest.mark.asyncio
    async def test_execute_partial_cache_info(self, cache_status_use_case, mock_dependency_container):
        """Test de manejo de información parcial del caché"""
        # Arrange - información incompleta del caché
        mock_dependency_container.cache_service.cache_info = {
            'exists': True,
            'size_bytes': 1024
            # Faltan otros campos
        }
        
        # Act
        result = await cache_status_use_case.execute()
        
        # Assert
        assert result.exists is True
        assert result.size_bytes == 1024
        assert result.size_mb == 0.0  # Valor por defecto
        assert result.embeddings_count == 0  # Valor por defecto
        assert result.file_path is None  # Valor por defecto
        assert result.last_modified is None  # Valor por defecto
    
    @pytest.mark.asyncio
    async def test_execute_cache_service_error(self, cache_status_use_case, mock_dependency_container):
        """Test de manejo de errores del servicio de caché"""
        # Arrange
        error_message = "Cache service unavailable"
        
        async def failing_get_cache_info():
            raise Exception(error_message)
        
        mock_dependency_container.cache_service.get_cache_info = failing_get_cache_info
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await cache_status_use_case.execute()
        
        assert str(exc_info.value) == error_message