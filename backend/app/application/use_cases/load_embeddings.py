from typing import List, Optional, TYPE_CHECKING
from ..dto.embedding_dto import EmbeddingResponseDTO, CacheStatusDTO

if TYPE_CHECKING:
    from ...infrastructure.config.dependency_container import DependencyContainer

class LoadEmbeddingsUseCase:
    """Caso de uso para cargar embeddings"""
    
    def __init__(self, dependency_container: 'DependencyContainer'):
        self.dependency_container = dependency_container
    
    async def execute(
        self, 
        csv_file_path: str, 
        cache_file_path: Optional[str] = None,
        force_regenerate: bool = False
    ) -> EmbeddingResponseDTO:
        """Ejecuta la carga de embeddings
        
        Args:
            csv_file_path: Ruta al archivo CSV
            cache_file_path: Ruta opcional del archivo de caché
            force_regenerate: Si forzar regeneración de embeddings
            
        Returns:
            DTO con información de embeddings generados
        """
        # Obtener el manager con la configuración específica
        embedding_manager = self.dependency_container.get_embedding_manager(cache_file_path)
        
        # Cargar o generar embeddings
        embeddings = await embedding_manager.load_or_generate_embeddings(
            csv_path=csv_file_path,
            force_regenerate=force_regenerate
        )
        
        # Transformar a DTO
        return EmbeddingResponseDTO(
            success=True,
            message=f"Embeddings procesados exitosamente desde {csv_file_path}",
            embeddings_count=len(embeddings),
            cache_used=not force_regenerate and await embedding_manager.cache_service.cache_exists(),
            model_info=embedding_manager.embedding_service.get_model_info()
        )

class GetCacheStatusUseCase:
    """Caso de uso para obtener el estado del caché"""
    
    def __init__(self, dependency_container: 'DependencyContainer'):
        self.dependency_container = dependency_container
    
    async def execute(self, cache_file_path: Optional[str] = None) -> CacheStatusDTO:
        """Obtiene el estado del caché
        
        Args:
            cache_file_path: Ruta del archivo de caché (opcional)
            
        Returns:
            DTO con información del estado del caché
        """
        # Obtener el servicio de caché específico
        cache_service = self.dependency_container.get_cache_service(cache_file_path)
        
        # Obtener información del caché
        cache_info = await cache_service.get_cache_info()
        
        return CacheStatusDTO(
            exists=cache_info.get("exists", False),
            file_path=cache_info.get("file_path", cache_file_path),
            size_bytes=cache_info.get("size_bytes", 0),
            size_mb=cache_info.get("size_mb", 0.0),
            embeddings_count=cache_info.get("embeddings_count", 0),
            last_modified=cache_info.get("last_modified")
        )