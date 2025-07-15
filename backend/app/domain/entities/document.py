from dataclasses import dataclass, field
from typing import List, Optional, Dict
import uuid

@dataclass
class Document:
    """Entidad que representa un documento del sistema"""
    id: str
    content: str
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.metadata is None:
            self.metadata = {}

@dataclass
class DocumentEmbedding:
    """Entidad que representa un embedding de un documento"""
    document_id: str
    content: str
    embedding: List[float]
    model: str = "text-embedding-3-small"
    
    def __post_init__(self):
        if not self.document_id:
            raise ValueError("document_id is required")
        if not self.embedding:
            raise ValueError("embedding is required")