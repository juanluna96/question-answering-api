from abc import ABC, abstractmethod
from typing import List

class EmbeddingService(ABC):
    """Puerto para generar embeddings usando servicios externos"""
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Genera un embedding para un texto
        
        Args:
            text: Texto para generar embedding
            
        Returns:
            Vector de embedding
        """
        pass
    
    @abstractmethod
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos en lote
        
        Args:
            texts: Lista de textos para generar embeddings
            
        Returns:
            Lista de vectores de embedding
        """
        pass