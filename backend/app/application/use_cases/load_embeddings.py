from typing import List, Optional
from ...domain.services.embedding_manager import EmbeddingManager
from ..dto.embedding_dto import EmbeddingResponseDTO, CacheStatusDTO

class LoadEmbeddingsUseCase:
    """Caso de uso para cargar embeddings"""
    
    def __init__(self, embedding_manager: EmbeddingManager):
        self.embedding_manager = embedding_manager
    
    async def execute(self, csv_path: str) -> List[EmbeddingResponseDTO]:
        """Ejecuta la carga de embeddings
        
        Args:
            csv_path: Ruta al archivo CSV
            
        Returns:
            Lista de DTOs con información de embeddings
        """
        embeddings = await self.embedding_manager.load_or_generate_embeddings(csv_path)
        
        return [
            EmbeddingResponseDTO(
                document_id=emb.document_id,
                content=emb.content[:100] + "..." if len(emb.content) > 100 else emb.content,
                embedding_size=len(emb.embedding),
                model=emb.model
            )
            for emb in embeddings
        ]

class GetCacheStatusUseCase:
    """Caso de uso para obtener el estado del caché"""
    
    def __init__(self, embedding_manager: EmbeddingManager):
        self.embedding_manager = embedding_manager
    
    async def execute(self, cache_file_path: Optional[str] = None) -> CacheStatusDTO:
        """Obtiene el estado del caché
        
        Args:
            cache_file_path: Ruta del archivo de caché (opcional)
            
        Returns:
            DTO con información del estado del caché
        """
        status = await self.embedding_manager.get_cache_status()
        
        return CacheStatusDTO(
            cache_exists=status["cache_exists"],
            embeddings_count=status["embeddings_count"],
            cache_file=cache_file_path
        )