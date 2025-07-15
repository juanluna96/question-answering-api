from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.document import DocumentEmbedding

class CacheService(ABC):
    """Puerto para manejar el caché de embeddings"""
    
    @abstractmethod
    async def save_embeddings(self, embeddings: List[DocumentEmbedding]) -> None:
        """Guarda embeddings en el caché
        
        Args:
            embeddings: Lista de embeddings a guardar
        """
        pass
    
    @abstractmethod
    async def load_embeddings(self) -> Optional[List[DocumentEmbedding]]:
        """Carga embeddings desde el caché
        
        Returns:
            Lista de embeddings o None si no existe caché
        """
        pass
    
    @abstractmethod
    async def cache_exists(self) -> bool:
        """Verifica si existe el caché
        
        Returns:
            True si existe el caché, False en caso contrario
        """
        pass