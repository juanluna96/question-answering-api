from typing import List, Optional
import logging
from ...domain.entities.document import DocumentEmbedding
from ...domain.ports.cache_service import CacheService

class EmbeddingCacheReader:
    """Servicio para leer embeddings desde el caché (Paso 1 de RAG)"""
    
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self._cached_embeddings: Optional[List[DocumentEmbedding]] = None
    
    async def load_embeddings_from_cache(self, force_reload: bool = False) -> List[DocumentEmbedding]:
        """
        Carga embeddings desde el caché (embeddings.pkl)
        
        Args:
            force_reload: Si forzar recarga desde archivo
            
        Returns:
            Lista de embeddings cargados desde caché
            
        Raises:
            Exception: Si no se puede cargar el caché
        """
        # Si ya están cargados en memoria y no se fuerza recarga
        if self._cached_embeddings is not None and not force_reload:
            logging.info(f"📋 Usando embeddings desde memoria: {len(self._cached_embeddings)} documentos")
            return self._cached_embeddings
        
        # Verificar si existe el caché
        cache_exists = await self.cache_service.cache_exists()
        if not cache_exists:
            raise Exception("No se encontró el archivo de caché de embeddings (embeddings.pkl)")
        
        logging.info("📦 Cargando embeddings desde caché...")
        
        # Cargar embeddings desde archivo
        embeddings = await self.cache_service.load_embeddings()
        
        if not embeddings:
            raise Exception("El archivo de caché está vacío o corrupto")
        
        # Guardar en memoria para futuras consultas
        self._cached_embeddings = embeddings
        
        logging.info(f"✅ Cargados {len(embeddings)} embeddings desde caché")
        logging.info(f"📊 Dimensión de embeddings: {len(embeddings[0].embedding) if embeddings else 0}")
        
        return embeddings
    
    async def get_cache_stats(self) -> dict:
        """
        Obtiene estadísticas del caché cargado
        
        Returns:
            Diccionario con estadísticas del caché
        """
        if self._cached_embeddings is None:
            return {
                "loaded": False,
                "message": "Embeddings no cargados en memoria"
            }
        
        embeddings = self._cached_embeddings
        
        return {
            "loaded": True,
            "total_documents": len(embeddings),
            "embedding_dimension": len(embeddings[0].embedding) if embeddings else 0,
            "average_content_length": sum(len(emb.content) for emb in embeddings) / len(embeddings) if embeddings else 0,
            "sample_document_ids": [emb.document_id for emb in embeddings[:3]] if embeddings else [],
            "models_used": list(set(emb.model for emb in embeddings)) if embeddings else []
        }
    
    def clear_cache(self):
        """
        Limpia el caché de memoria
        """
        self._cached_embeddings = None
        logging.info("🗑️ Caché de embeddings limpiado de memoria")
    
    def is_cache_loaded(self) -> bool:
        """
        Verifica si los embeddings están cargados en memoria
        
        Returns:
            True si están cargados, False en caso contrario
        """
        return self._cached_embeddings is not None