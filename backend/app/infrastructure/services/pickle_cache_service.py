import pickle
import asyncio
import os
import time
from typing import List, Optional
from ...domain.entities.document import DocumentEmbedding
from ...domain.ports.cache_service import CacheService

class PickleCacheService(CacheService):
    """Adaptador para manejar caché de embeddings usando pickle"""
    
    def __init__(self, cache_file_path: str):
        """Inicializa el servicio de caché
        
        Args:
            cache_file_path: Ruta del archivo de caché
        """
        self.cache_file_path = cache_file_path
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
    
    async def save_embeddings(self, embeddings: List[DocumentEmbedding]) -> None:
        """Guarda embeddings en el caché
        
        Args:
            embeddings: Lista de embeddings a guardar
            
        Raises:
            Exception: Si hay error al guardar
        """
        try:
            # Ejecutar la escritura en un hilo separado para no bloquear
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._save_embeddings_sync, embeddings)
            
        except Exception as e:
            raise Exception(f"Error al guardar embeddings en caché: {str(e)}")
    
    async def load_embeddings(self) -> Optional[List[DocumentEmbedding]]:
        """Carga embeddings desde el caché
        
        Returns:
            Lista de embeddings o None si no existe caché
            
        Raises:
            Exception: Si hay error al cargar
        """
        try:
            if not await self.cache_exists():
                return None
            
            # Ejecutar la lectura en un hilo separado para no bloquear
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, self._load_embeddings_sync)
            
            return embeddings
            
        except Exception as e:
            raise Exception(f"Error al cargar embeddings desde caché: {str(e)}")
    
    async def cache_exists(self) -> bool:
        """Verifica si existe el caché
        
        Returns:
            True si existe el caché, False en caso contrario
        """
        return os.path.exists(self.cache_file_path) and os.path.getsize(self.cache_file_path) > 0
    
    def _save_embeddings_sync(self, embeddings: List[DocumentEmbedding]) -> None:
        """Guarda embeddings de forma síncrona
        
        Args:
            embeddings: Lista de embeddings a guardar
        """
        # Preparar datos para serialización
        cache_data = {
            "embeddings": embeddings,
            "metadata": {
                "count": len(embeddings),
                "created_at": time.time(),
                "version": "1.0"
            }
        }
        
        # Guardar con archivo temporal para atomicidad
        temp_file = self.cache_file_path + ".tmp"
        
        with open(temp_file, 'wb') as f:
            pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # Mover archivo temporal al final
        os.rename(temp_file, self.cache_file_path)
    
    def _load_embeddings_sync(self) -> List[DocumentEmbedding]:
        """Carga embeddings de forma síncrona
        
        Returns:
            Lista de embeddings
        """
        with open(self.cache_file_path, 'rb') as f:
            cache_data = pickle.load(f)
        
        # Verificar formato del caché
        if isinstance(cache_data, dict) and "embeddings" in cache_data:
            return cache_data["embeddings"]
        elif isinstance(cache_data, list):
            # Formato legacy - lista directa
            return cache_data
        else:
            raise ValueError("Formato de caché no válido")
    
    async def clear_cache(self) -> None:
        """Limpia el caché eliminando el archivo
        
        Raises:
            Exception: Si hay error al eliminar
        """
        try:
            if await self.cache_exists():
                os.remove(self.cache_file_path)
        except Exception as e:
            raise Exception(f"Error al limpiar caché: {str(e)}")
    
    async def get_cache_info(self) -> dict:
        """Obtiene información del caché
        
        Returns:
            Información del caché
        """
        if not await self.cache_exists():
            return {
                "exists": False,
                "file_path": self.cache_file_path,
                "size_bytes": 0,
                "embeddings_count": 0
            }
        
        try:
            file_size = os.path.getsize(self.cache_file_path)
            embeddings = await self.load_embeddings()
            count = len(embeddings) if embeddings else 0
            
            return {
                "exists": True,
                "file_path": self.cache_file_path,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "embeddings_count": count,
                "last_modified": os.path.getmtime(self.cache_file_path)
            }
            
        except Exception as e:
            return {
                "exists": True,
                "file_path": self.cache_file_path,
                "error": str(e)
            }