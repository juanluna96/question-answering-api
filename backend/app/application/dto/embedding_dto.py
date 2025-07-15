from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class EmbeddingResponseDTO(BaseModel):
    """DTO para respuesta de embeddings"""
    success: bool
    message: str
    embeddings_count: int
    cache_used: bool
    model_info: Dict[str, Any]
    
class CacheStatusDTO(BaseModel):
    """DTO para estado del caché"""
    exists: bool
    file_path: Optional[str] = None
    size_bytes: int = 0
    size_mb: float = 0.0
    embeddings_count: int = 0
    last_modified: Optional[float] = None
    
class LoadEmbeddingsRequestDTO(BaseModel):
    """DTO para solicitud de carga de embeddings"""
    csv_file_path: str = Field(..., description="Ruta al archivo CSV")
    cache_file_path: Optional[str] = Field(None, description="Ruta opcional del archivo de caché")
    force_regenerate: bool = Field(False, description="Forzar regeneración de embeddings")