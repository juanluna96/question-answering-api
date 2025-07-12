from abc import ABC, abstractmethod
from typing import List
from ..entities.document import Document

class DocumentRepository(ABC):
    """Puerto para cargar documentos desde fuentes externas"""
    
    @abstractmethod
    async def load_documents(self, file_path: str) -> List[Document]:
        """Carga documentos desde un archivo
        
        Args:
            file_path: Ruta al archivo de documentos
            
        Returns:
            Lista de documentos cargados
        """
        pass