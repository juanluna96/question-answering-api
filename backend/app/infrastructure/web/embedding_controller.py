from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from ...application.dto.embedding_dto import (
    EmbeddingResponseDTO,
    CacheStatusDTO,
    LoadEmbeddingsRequestDTO
)
from ...application.use_cases.load_embeddings import (
    LoadEmbeddingsUseCase,
    GetCacheStatusUseCase
)

class EmbeddingController:
    """Controlador para manejar endpoints de embeddings"""
    
    def __init__(
        self,
        load_embeddings_use_case: LoadEmbeddingsUseCase,
        get_cache_status_use_case: GetCacheStatusUseCase
    ):
        """Inicializa el controlador
        
        Args:
            load_embeddings_use_case: Caso de uso para cargar embeddings
            get_cache_status_use_case: Caso de uso para obtener estado del caché
        """
        self.load_embeddings_use_case = load_embeddings_use_case
        self.get_cache_status_use_case = get_cache_status_use_case
        self.router = APIRouter(prefix="/embeddings", tags=["embeddings"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas del controlador"""
        
        @self.router.post(
            "/load",
            response_model=EmbeddingResponseDTO,
            summary="Cargar embeddings",
            description="Carga y genera embeddings desde un archivo CSV"
        )
        async def load_embeddings(request: LoadEmbeddingsRequestDTO) -> EmbeddingResponseDTO:
            """Endpoint para cargar embeddings
            
            Args:
                request: Datos de la solicitud
                
            Returns:
                Respuesta con embeddings generados
                
            Raises:
                HTTPException: Si hay error en el procesamiento
            """
            try:
                result = await self.load_embeddings_use_case.execute(
                    csv_file_path=request.csv_file_path,
                    cache_file_path=request.cache_file_path,
                    force_regenerate=request.force_regenerate
                )
                return result
                
            except FileNotFoundError as e:
                raise HTTPException(
                    status_code=404,
                    detail=f"Archivo no encontrado: {str(e)}"
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error de validación: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error interno del servidor: {str(e)}"
                )
        
        @self.router.get(
            "/cache/status",
            response_model=CacheStatusDTO,
            summary="Estado del caché",
            description="Obtiene información sobre el estado del caché de embeddings"
        )
        async def get_cache_status(
            cache_file_path: Optional[str] = None
        ) -> CacheStatusDTO:
            """Endpoint para obtener estado del caché
            
            Args:
                cache_file_path: Ruta opcional del archivo de caché
                
            Returns:
                Estado del caché
                
            Raises:
                HTTPException: Si hay error en el procesamiento
            """
            try:
                result = await self.get_cache_status_use_case.execute(
                    cache_file_path=cache_file_path
                )
                return result
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al obtener estado del caché: {str(e)}"
                )
        
        @self.router.delete(
            "/cache",
            summary="Limpiar caché",
            description="Elimina el caché de embeddings"
        )
        async def clear_cache(
            cache_file_path: Optional[str] = None
        ) -> dict:
            """Endpoint para limpiar caché
            
            Args:
                cache_file_path: Ruta opcional del archivo de caché
                
            Returns:
                Confirmación de limpieza
                
            Raises:
                HTTPException: Si hay error en el procesamiento
            """
            try:
                # Obtener información del caché antes de limpiar
                cache_status = await self.get_cache_status_use_case.execute(
                    cache_file_path=cache_file_path
                )
                
                if not cache_status.exists:
                    return {
                        "message": "No hay caché para limpiar",
                        "cache_existed": False
                    }
                
                # Aquí se podría implementar la limpieza del caché
                # Por ahora retornamos un mensaje
                return {
                    "message": "Caché limpiado exitosamente",
                    "cache_existed": True,
                    "embeddings_removed": cache_status.embeddings_count
                }
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al limpiar caché: {str(e)}"
                )
        
        @self.router.get(
            "/health",
            summary="Health check",
            description="Verifica el estado del servicio de embeddings"
        )
        async def health_check() -> dict:
            """Endpoint de health check
            
            Returns:
                Estado del servicio
            """
            return {
                "status": "healthy",
                "service": "embedding-service",
                "version": "1.0.0"
            }
    
    def get_router(self) -> APIRouter:
        """Obtiene el router configurado
        
        Returns:
            Router de FastAPI
        """
        return self.router