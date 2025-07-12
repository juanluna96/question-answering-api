from pydantic import BaseModel
from typing import Optional

class EmbeddingResponseDTO(BaseModel):
    """DTO para respuesta de embeddings"""
    document_id: str
    content: str
    embedding_size: int
    model: str
    
class CacheStatusDTO(BaseModel):
    """DTO para estado del caché"""
    cache_exists: bool
    embeddings_count: int
    cache_file: Optional[str] = None
    
class LoadEmbeddingsRequestDTO(BaseModel):
    """DTO para solicitud de carga de embeddings"""
    csv_path: Optional[str] = None  # Si no se proporciona, usa el default de configuración