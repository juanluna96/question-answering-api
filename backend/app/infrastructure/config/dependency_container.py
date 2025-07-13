import os
from typing import Optional
from dotenv import load_dotenv
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
    
    def __init__(self):
        """Inicializa el contenedor"""
        # Cargar variables de entorno desde .env (override=True para sobrescribir variables del sistema)
        load_dotenv(override=True)
        self._instances = {}
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """Carga la configuración desde variables de entorno
        
        Returns:
            Diccionario de configuración
        """
        print("Cargando configuración...")
        print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
        print("OPENAI_MODEL:", os.getenv("OPENAI_MODEL", "text-embedding-3-small"))
        print("DEFAULT_CACHE_PATH:", os.getenv("DEFAULT_CACHE_PATH", "./data/cache/embeddings.pkl"))
        print("MAX_FILE_SIZE_MB:", os.getenv("MAX_FILE_SIZE_MB", "50"))
        print("BATCH_SIZE:", os.getenv("BATCH_SIZE", "100"))
    
        return {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "openai_model": os.getenv("OPENAI_MODEL", "text-embedding-3-small"),
            "default_cache_path": os.getenv(
                "DEFAULT_CACHE_PATH", 
                "./data/cache/embeddings.pkl"
            ),
            "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "50")),
            "batch_size": int(os.getenv("BATCH_SIZE", "100"))
        }
    
    def get_csv_repository(self) -> CSVDocumentRepository:
        """Obtiene una instancia del repositorio CSV"""
        max_file_size = int(self._config.get('max_file_size_mb', 50))
        return CSVDocumentRepository(max_file_size_mb=max_file_size)
    
    def get_embedding_service(self) -> OpenAIEmbeddingService:
        """Obtiene el servicio de embeddings
        
        Returns:
            Instancia del servicio
            
        Raises:
            ValueError: Si no está configurada la API key
        """
        if "embedding_service" not in self._instances:
            api_key = self._config["openai_api_key"]
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY no está configurada en las variables de entorno"
                )
            
            self._instances["embedding_service"] = OpenAIEmbeddingService(
                api_key=api_key,
                model=self._config["openai_model"]
            )
        return self._instances["embedding_service"]
    
    def get_cache_service(self, cache_file_path: Optional[str] = None) -> PickleCacheService:
        """Obtiene el servicio de caché
        
        Args:
            cache_file_path: Ruta opcional del archivo de caché
            
        Returns:
            Instancia del servicio
        """
        cache_path = cache_file_path or self._config["default_cache_path"]
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