import asyncio
import logging
from typing import List, Tuple, Dict, Optional, Any
from ...domain.entities.document import DocumentEmbedding
from ...domain.ports.embedding_service import EmbeddingService
from ...domain.ports.cache_service import CacheService
from .embedding_cache_reader import EmbeddingCacheReader
from .semantic_similarity_calculator import SemanticSimilarityCalculator
from .lexical_similarity_calculator import LexicalSimilarityCalculator
from .score_combiner import ScoreCombiner

class RAGRetrievalService:
    """Servicio principal de recuperación RAG que integra todos los componentes (Paso 5 de RAG)"""
    
    def __init__(
        self,
        embedding_cache_reader,
        semantic_similarity_calculator,
        lexical_similarity_calculator,
        score_combiner,
        context_builder,
        context_limiter
    ):
        self.logger = logging.getLogger(__name__)
        
        # Inicializar componentes
        self.cache_reader = embedding_cache_reader
        self.semantic_calculator = semantic_similarity_calculator
        self.lexical_calculator = lexical_similarity_calculator
        self.score_combiner = score_combiner
        self.context_builder = context_builder
        self.context_limiter = context_limiter
        
        # Estado del servicio
        self._is_initialized = False
        self._documents_cache: List[DocumentEmbedding] = []
        
        self.logger.info("🚀 RAGRetrievalService inicializado con todos los componentes")
    
    async def initialize(self) -> bool:
        """
        Inicializa el servicio cargando los embeddings
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            self.logger.info("🔄 Inicializando RAGRetrievalService...")
            
            # Cargar embeddings desde el caché
            embeddings_data = await self.cache_reader.load_embeddings_from_cache()
            
            if not embeddings_data:
                self.logger.error("❌ No se pudieron cargar los embeddings")
                return False
            
            # Guardar documentos del caché
            self._documents_cache = embeddings_data
            
            # Obtener estadísticas
            stats = await self.cache_reader.get_cache_stats()
            self.logger.info(f"📊 Embeddings cargados: {stats['total_embeddings']} documentos")
            self.logger.info(f"📊 Tamaño promedio de embedding: {stats['avg_embedding_size']:.0f} dimensiones")
            
            self._is_initialized = True
            self.logger.info("✅ RAGRetrievalService inicializado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error al inicializar RAGRetrievalService: {str(e)}")
            return False
    
    async def search_documents(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> List[Tuple[DocumentEmbedding, float, Dict[str, Any]]]:
        """
        Busca documentos relevantes usando RAG híbrido
        
        Args:
            query: Consulta de búsqueda
            top_k: Número de documentos más relevantes
            use_hybrid: Si usar búsqueda híbrida (semántica + lexical)
            
        Returns:
            Lista de documentos con scores y detalles
        """
        if not self._is_initialized:
            raise RuntimeError("El servicio no ha sido inicializado. Llama a initialize() primero.")
        
        if not self._documents_cache:
            self.logger.warning("⚠️ No hay documentos en el caché")
            return []
        
        self.logger.info(f"🔍 Buscando documentos para: '{query}' (top_k={top_k}, hybrid={use_hybrid})")
        
        try:
            if use_hybrid:
                return await self._hybrid_search(query, top_k)
            else:
                return await self._semantic_only_search(query, top_k)
                
        except Exception as e:
            self.logger.error(f"❌ Error en búsqueda: {str(e)}")
            return []
    
    async def _hybrid_search(
        self,
        query: str,
        top_k: int
    ) -> List[Tuple[DocumentEmbedding, float, Dict[str, Any]]]:
        """
        Realiza búsqueda híbrida (semántica + lexical)
        """
        self.logger.info("🔄 Ejecutando búsqueda híbrida...")
        
        # Ejecutar búsquedas en paralelo para mejor rendimiento
        semantic_task = self.semantic_calculator.calculate_query_similarity(
            query, self._documents_cache
        )
        
        lexical_task = self.lexical_calculator.calculate_query_similarity(
            query, self._documents_cache
        )
        
        # Esperar ambos resultados
        semantic_results, lexical_results = await asyncio.gather(
            semantic_task, lexical_task
        )
        
        self.logger.info(f"📊 Resultados semánticos: {len(semantic_results)}, lexicales: {len(lexical_results)}")
        
        # Combinar scores
        combined_results = await self.score_combiner.get_top_documents(
            semantic_results, lexical_results, top_k
        )
        
        return combined_results
    
    async def _semantic_only_search(
        self,
        query: str,
        top_k: int
    ) -> List[Tuple[DocumentEmbedding, float, Dict[str, Any]]]:
        """
        Realiza búsqueda solo semántica
        """
        self.logger.info("🔄 Ejecutando búsqueda semántica únicamente...")
        
        all_semantic_results = await self.semantic_calculator.calculate_query_similarity(
            query, self._documents_cache
        )
        
        # Ordenar y tomar top_k
        all_semantic_results.sort(key=lambda x: x[1], reverse=True)
        semantic_results = all_semantic_results[:top_k]
        
        # Convertir a formato compatible con resultados híbridos
        formatted_results = []
        for doc, score in semantic_results:
            score_details = {
                "semantic_score": score,
                "lexical_score": 0.0,
                "combined_score": score,
                "semantic_weight": 1.0,
                "lexical_weight": 0.0
            }
            formatted_results.append((doc, score, score_details))
        
        return formatted_results