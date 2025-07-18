from typing import Optional
from .settings import Settings
from ...domain.services.embedding_manager import EmbeddingManager
from ...application.use_cases.load_embeddings import (
    LoadEmbeddingsUseCase,
    GetCacheStatusUseCase
)
from ..repositories.csv_document_repository import CSVDocumentRepository
from ..services.openai_embedding_service import OpenAIEmbeddingService
from ..services.pickle_cache_service import PickleCacheService
from ..web.embedding_controller import EmbeddingController

class DependencyContainer:
    """Contenedor de dependencias para inyección de dependencias"""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Inicializa el contenedor
        
        Args:
            settings: Instancia de configuración. Si no se proporciona, se crea una nueva.
        """
        self._instances = {}
        self._settings = settings or Settings()
        # Mantener compatibilidad con el formato anterior
        self._config = {
            "openai_api_key": self._settings.openai_api_key,
            "openai_model": self._settings.embedding_model,  # Para embeddings
            "default_cache_path": self._settings.embedding_cache_path,
            "max_file_size_mb": self._settings.max_file_size_mb,
            "batch_size": self._settings.batch_size
        }
    
    def get_csv_repository(self) -> CSVDocumentRepository:
        """Obtiene una instancia del repositorio CSV"""
        return CSVDocumentRepository(max_file_size_mb=self._settings.max_file_size_mb)
    
    def get_embedding_service(self) -> OpenAIEmbeddingService:
        """Obtiene el servicio de embeddings
        
        Returns:
            Instancia del servicio
            
        Raises:
            ValueError: Si no está configurada la API key
        """
        if "embedding_service" not in self._instances:
            if not self._settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY no está configurada en las variables de entorno"
                )
            
            self._instances["embedding_service"] = OpenAIEmbeddingService(
                api_key=self._settings.openai_api_key,
                model=self._settings.embedding_model
            )
        return self._instances["embedding_service"]
    
    def get_cache_service(self, cache_file_path: Optional[str] = None) -> PickleCacheService:
        """Obtiene el servicio de caché
        
        Args:
            cache_file_path: Ruta opcional del archivo de caché
            
        Returns:
            Instancia del servicio
        """
        cache_path = cache_file_path or self._settings.embedding_cache_path
        cache_key = f"cache_service_{cache_path}"
        
        if cache_key not in self._instances:
            self._instances[cache_key] = PickleCacheService(cache_path)
        return self._instances[cache_key]
    
    def get_embedding_manager(self, cache_file_path: Optional[str] = None) -> EmbeddingManager:
        """Obtiene el manager de embeddings
        
        Args:
            cache_file_path: Ruta opcional del archivo de caché
            
        Returns:
            Instancia del manager
        """
        manager_key = f"embedding_manager_{cache_file_path or 'default'}"
        
        if manager_key not in self._instances:
            self._instances[manager_key] = EmbeddingManager(
                document_repo=self.get_csv_repository(),
                embedding_service=self.get_embedding_service(),
                cache_service=self.get_cache_service(cache_file_path)
            )
        return self._instances[manager_key]
    
    def get_load_embeddings_use_case(self) -> LoadEmbeddingsUseCase:
        """Obtiene el caso de uso para cargar embeddings
        
        Returns:
            Instancia del caso de uso
        """
        if "load_embeddings_use_case" not in self._instances:
            self._instances["load_embeddings_use_case"] = LoadEmbeddingsUseCase(
                dependency_container=self
            )
        return self._instances["load_embeddings_use_case"]
    
    def get_cache_status_use_case(self) -> GetCacheStatusUseCase:
        """Obtiene el caso de uso para obtener estado del caché
        
        Returns:
            Instancia del caso de uso
        """
        if "cache_status_use_case" not in self._instances:
            self._instances["cache_status_use_case"] = GetCacheStatusUseCase(
                dependency_container=self
            )
        return self._instances["cache_status_use_case"]
    
    def get_embedding_controller(self) -> EmbeddingController:
        """Obtiene el controlador de embeddings
        
        Returns:
            Instancia del controlador
        """
        if "embedding_controller" not in self._instances:
            self._instances["embedding_controller"] = EmbeddingController(
                load_embeddings_use_case=self.get_load_embeddings_use_case(),
                get_cache_status_use_case=self.get_cache_status_use_case()
            )
        return self._instances["embedding_controller"]
    
    def get_config(self) -> dict:
        """Obtiene la configuración
        
        Returns:
            Diccionario de configuración
        """
        return self._config.copy()
    
    def get_settings(self) -> Settings:
        """Obtiene la instancia de configuración completa
        
        Returns:
            Instancia de Settings
        """
        return self._settings
    
    def clear_instances(self) -> None:
        """Limpia todas las instancias (útil para testing)"""
        self._instances.clear()
    
    def override_config(self, **kwargs) -> None:
        """Sobrescribe configuración (útil para testing)
        
        Args:
            **kwargs: Configuraciones a sobrescribir
        """
        self._config.update(kwargs)
        # Limpiar instancias que dependan de la configuración
        keys_to_clear = [
            "embedding_service", 
            "cache_service", 
            "embedding_manager",
            "load_embeddings_use_case",
            "cache_status_use_case",
            "embedding_controller"
        ]
        for key in keys_to_clear:
            if key in self._instances:
                del self._instances[key]