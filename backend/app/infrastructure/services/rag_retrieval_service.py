import asyncio
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
        embedding_service: EmbeddingService,
        cache_service: CacheService,
        semantic_weight: float = 0.7,
        lexical_weight: float = 0.3
    ):
        """
        Inicializa el servicio de recuperación RAG
        
        Args:
            embedding_service: Servicio para generar embeddings
            cache_service: Servicio de caché para embeddings
            semantic_weight: Peso para similitud semántica
            lexical_weight: Peso para similitud lexical
        """
        self.embedding_service = embedding_service
        
        # Inicializar componentes
        self.cache_reader = EmbeddingCacheReader(cache_service)
        self.semantic_calculator = SemanticSimilarityCalculator(embedding_service)
        self.lexical_calculator = LexicalSimilarityCalculator()
        self.score_combiner = ScoreCombiner(semantic_weight, lexical_weight)
        
        # Estado del servicio
        self._is_initialized = False
        self._documents_cache: List[DocumentEmbedding] = []
        
        print(f"🚀 RAGRetrievalService inicializado con pesos: semántico={semantic_weight}, lexical={lexical_weight}")
    
    async def initialize(self) -> bool:
        """
        Inicializa el servicio cargando los embeddings
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            print("🔄 Inicializando RAGRetrievalService...")
            
            # Cargar embeddings desde el caché
            embeddings_data = await self.cache_reader.load_embeddings_from_cache()
            
            if not embeddings_data:
                print("❌ No se pudieron cargar los embeddings")
                return False
            
            # Guardar documentos del caché
            self._documents_cache = embeddings_data
            
            # Obtener estadísticas
            stats = await self.cache_reader.get_cache_stats()
            print(f"📊 Embeddings cargados: {stats['total_embeddings']} documentos")
            print(f"📊 Tamaño promedio de embedding: {stats['avg_embedding_size']:.0f} dimensiones")
            
            self._is_initialized = True
            print("✅ RAGRetrievalService inicializado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al inicializar RAGRetrievalService: {str(e)}")
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
            print("⚠️ No hay documentos en el caché")
            return []
        
        print(f"🔍 Buscando documentos para: '{query}' (top_k={top_k}, hybrid={use_hybrid})")
        
        try:
            if use_hybrid:
                return await self._hybrid_search(query, top_k)
            else:
                return await self._semantic_only_search(query, top_k)
                
        except Exception as e:
            print(f"❌ Error en búsqueda: {str(e)}")
            return []
    
    async def _hybrid_search(
        self,
        query: str,
        top_k: int
    ) -> List[Tuple[DocumentEmbedding, float, Dict[str, Any]]]:
        """
        Realiza búsqueda híbrida (semántica + lexical)
        """
        print("🔄 Ejecutando búsqueda híbrida...")
        
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
        
        print(f"📊 Resultados semánticos: {len(semantic_results)}, lexicales: {len(lexical_results)}")
        
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
        print("🔄 Ejecutando búsqueda semántica únicamente...")
        
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
    
    async def analyze_query_performance(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Analiza el rendimiento de una consulta comparando métodos
        
        Args:
            query: Consulta a analizar
            top_k: Número de documentos a recuperar
            
        Returns:
            Análisis detallado del rendimiento
        """
        if not self._is_initialized:
            raise RuntimeError("El servicio no ha sido inicializado")
        
        print(f"📊 Analizando rendimiento para: '{query}'")
        
        import time
        
        # Medir tiempo de búsqueda semántica
        start_time = time.time()
        semantic_results = await self._semantic_only_search(query, top_k)
        semantic_time = time.time() - start_time
        
        # Medir tiempo de búsqueda híbrida
        start_time = time.time()
        hybrid_results = await self._hybrid_search(query, top_k)
        hybrid_time = time.time() - start_time
        
        # Analizar distribución de scores híbridos
        score_analysis = await self.score_combiner.analyze_score_distribution(hybrid_results)
        
        analysis = {
            "query": query,
            "top_k": top_k,
            "total_documents": len(self._documents_cache),
            "performance": {
                "semantic_only_time": semantic_time,
                "hybrid_time": hybrid_time,
                "time_difference": hybrid_time - semantic_time
            },
            "results_comparison": {
                "semantic_results_count": len(semantic_results),
                "hybrid_results_count": len(hybrid_results)
            },
            "score_distribution": score_analysis,
            "top_results": {
                "semantic": [
                    {
                        "document_id": doc.document_id,
                        "score": score,
                        "content_preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                    }
                    for doc, score, _ in semantic_results[:3]
                ],
                "hybrid": [
                    {
                        "document_id": doc.document_id,
                        "combined_score": score,
                        "semantic_score": details["semantic_score"],
                        "lexical_score": details["lexical_score"],
                        "content_preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                    }
                    for doc, score, details in hybrid_results[:3]
                ]
            }
        }
        
        return analysis
    
    async def get_service_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del servicio
        
        Returns:
            Diccionario con información del estado
        """
        cache_stats = await self.cache_reader.get_cache_stats() if self._is_initialized else {}
        combiner_config = self.score_combiner.get_configuration()
        
        status = {
            "initialized": self._is_initialized,
            "documents_loaded": len(self._documents_cache),
            "cache_stats": cache_stats,
            "score_weights": combiner_config,
            "components": {
                "cache_reader": "✅ Activo" if self._is_initialized else "❌ No inicializado",
                "semantic_calculator": "✅ Activo",
                "lexical_calculator": "✅ Activo",
                "score_combiner": "✅ Activo"
            }
        }
        
        return status
    
    def update_search_weights(self, semantic_weight: float, lexical_weight: float):
        """
        Actualiza los pesos de búsqueda
        
        Args:
            semantic_weight: Nuevo peso semántico
            lexical_weight: Nuevo peso lexical
        """
        self.score_combiner.update_weights(semantic_weight, lexical_weight)
        print(f"🔄 Pesos de búsqueda actualizados: semántico={semantic_weight}, lexical={lexical_weight}")
    
    async def refresh_cache(self) -> bool:
        """
        Refresca el caché de embeddings
        
        Returns:
            True si el refresh fue exitoso
        """
        print("🔄 Refrescando caché de embeddings...")
        
        try:
            # Limpiar caché actual
            self.cache_reader.clear_cache()
            self._documents_cache.clear()
            self._is_initialized = False
            
            # Reinicializar
            return await self.initialize()
            
        except Exception as e:
            print(f"❌ Error al refrescar caché: {str(e)}")
            return False