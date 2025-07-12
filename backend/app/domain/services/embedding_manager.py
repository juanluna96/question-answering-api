from typing import List
from ..entities.document import Document, DocumentEmbedding
from ..ports.document_repository import DocumentRepository
from ..ports.embedding_service import EmbeddingService
from ..ports.cache_service import CacheService

class EmbeddingManager:
    """Servicio de dominio que maneja la lógica de embeddings"""
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        embedding_service: EmbeddingService,
        cache_service: CacheService
    ):
        self.document_repo = document_repo
        self.embedding_service = embedding_service
        self.cache_service = cache_service
    
    async def load_or_generate_embeddings(self, csv_path: str) -> List[DocumentEmbedding]:
        """Carga embeddings desde caché o los genera si no existen
        
        Args:
            csv_path: Ruta al archivo CSV con documentos
            
        Returns:
            Lista de embeddings de documentos
        """
        # Verificar si existe caché
        if await self.cache_service.cache_exists():
            print("📦 Cargando embeddings desde caché...")
            cached_embeddings = await self.cache_service.load_embeddings()
            if cached_embeddings:
                print(f"✅ Cargados {len(cached_embeddings)} embeddings desde caché")
                return cached_embeddings
        
        print("🔄 Generando nuevos embeddings...")
        # Cargar documentos y generar embeddings
        documents = await self.document_repo.load_documents(csv_path)
        print(f"📄 Cargados {len(documents)} documentos")
        
        embeddings = await self._generate_embeddings_for_documents(documents)
        print(f"🧠 Generados {len(embeddings)} embeddings")
        
        # Guardar en caché
        await self.cache_service.save_embeddings(embeddings)
        print("💾 Embeddings guardados en caché")
        
        return embeddings
    
    async def _generate_embeddings_for_documents(self, documents: List[Document]) -> List[DocumentEmbedding]:
        """Genera embeddings para una lista de documentos
        
        Args:
            documents: Lista de documentos
            
        Returns:
            Lista de embeddings generados
        """
        texts = [doc.content for doc in documents]
        
        # Generar embeddings en lote para eficiencia
        embedding_vectors = await self.embedding_service.generate_embeddings_batch(texts)
        
        return [
            DocumentEmbedding(
                document_id=doc.id,
                content=doc.content,
                embedding=embedding
            )
            for doc, embedding in zip(documents, embedding_vectors)
        ]
    
    async def get_cache_status(self) -> dict:
        """Obtiene el estado del caché
        
        Returns:
            Diccionario con información del estado del caché
        """
        cache_exists = await self.cache_service.cache_exists()
        
        if cache_exists:
            embeddings = await self.cache_service.load_embeddings()
            count = len(embeddings) if embeddings else 0
        else:
            count = 0
            
        return {
            "cache_exists": cache_exists,
            "embeddings_count": count
        }