from typing import Optional
from ...domain.ports.question_service_port import QuestionServicePort
from ...infrastructure.services.rag_question_service import RAGQuestionService

from ...infrastructure.services.rag_generation_service import RAGGenerationService
from ...infrastructure.services.rag_retrieval_service import RAGRetrievalService
from ...infrastructure.services.openai_generation_service import OpenAIGenerationService
from ...infrastructure.services.openai_embedding_service import OpenAIEmbeddingService
from ...infrastructure.services.embedding_cache_reader import EmbeddingCacheReader
from ...infrastructure.config.settings import Settings
from ...infrastructure.services.pickle_cache_service import PickleCacheService

class QuestionServiceFactory:
    """Factory para crear instancias del servicio de preguntas"""
    
    def __init__(self, settings: Settings):
        """
        Inicializa el factory con la configuración
        
        Args:
            settings: Configuración de la aplicación
        """
        self._settings = settings
        self._rag_question_service: Optional[RAGQuestionService] = None

    
    async def create_rag_question_service(self) -> RAGQuestionService:
        """
        Crea una instancia del servicio RAG de preguntas con todas sus dependencias
        
        Returns:
            RAGQuestionService: Servicio configurado e inicializado
        """
        if self._rag_question_service is None:
            # Crear servicio de generación OpenAI
            openai_generation = OpenAIGenerationService(
                api_key=self._settings.openai_api_key,
                model=self._settings.openai_model,
                max_tokens=self._settings.max_tokens,
                temperature=self._settings.temperature
            )
            
            # Crear servicio de embeddings OpenAI
            openai_embedding = OpenAIEmbeddingService(
                api_key=self._settings.openai_api_key,
                model=self._settings.embedding_model
            )
            
            # Crear servicio de caché
            cache_service = PickleCacheService(
                cache_file_path=self._settings.embedding_cache_path
            )
            
            # Crear lector de cache de embeddings
            embedding_cache_reader = EmbeddingCacheReader(
                cache_service=cache_service
            )
            
            # Crear calculadoras de similitud
            from ...infrastructure.services.semantic_similarity_calculator import SemanticSimilarityCalculator
            from ...infrastructure.services.lexical_similarity_calculator import LexicalSimilarityCalculator
            from ...infrastructure.services.score_combiner import ScoreCombiner
            from ...infrastructure.services.context_builder import ContextBuilder
            from ...infrastructure.services.context_limiter import ContextLimiter
            
            semantic_similarity_calculator = SemanticSimilarityCalculator(
                embedding_service=openai_embedding
            )
            
            lexical_similarity_calculator = LexicalSimilarityCalculator()
            
            score_combiner = ScoreCombiner(
                semantic_weight=0.7,
                lexical_weight=0.3
            )
            
            context_builder = ContextBuilder()
            
            context_limiter = ContextLimiter(
                max_tokens=self._settings.max_tokens
            )
            
            # Crear servicio de generación RAG
            rag_generation_service = RAGGenerationService(
                openai_service=openai_generation
            )
            
            # Crear servicio de recuperación RAG
            rag_retrieval_service = RAGRetrievalService(
                embedding_cache_reader=embedding_cache_reader,
                semantic_similarity_calculator=semantic_similarity_calculator,
                lexical_similarity_calculator=lexical_similarity_calculator,
                score_combiner=score_combiner,
                context_builder=context_builder,
                context_limiter=context_limiter
            )
            
            # Inicializar el servicio de recuperación
            initialization_success = await rag_retrieval_service.initialize()
            if not initialization_success:
                # Intentar crear embeddings automáticamente
                print("No se pudieron cargar embeddings desde caché. Intentando crear embeddings automáticamente...")
                
                # Definir la ruta del CSV fuera del bloque try
                csv_path = self._settings.documents_csv_path
                
                try:
                    # Importar dependencias necesarias
                    from ...infrastructure.config.dependency_container import DependencyContainer
                    
                    # Crear contenedor de dependencias y caso de uso
                    dependency_container = DependencyContainer(self._settings)
                    load_embeddings_use_case = dependency_container.get_load_embeddings_use_case()
                    
                    result = await load_embeddings_use_case.execute(
                        csv_file_path=csv_path,
                        cache_file_path=self._settings.embedding_cache_path,
                        force_regenerate=False
                    )
                    print(f"Embeddings creados exitosamente: {result.message}")
                    
                    # Limpiar caché en memoria para forzar recarga desde archivo
                    embedding_cache_reader.clear_cache()
                    
                    # Intentar inicializar nuevamente con force_reload
                    embeddings_data = await embedding_cache_reader.load_embeddings_from_cache(force_reload=True)
                    if embeddings_data:
                        rag_retrieval_service._documents_cache = embeddings_data
                        rag_retrieval_service._is_initialized = True
                        initialization_success = True
                    else:
                        initialization_success = False
                    if not initialization_success:
                        raise RuntimeError("Falló la inicialización después de crear embeddings")
                        
                except Exception as create_error:
                    raise RuntimeError(
                        f"No se pudo inicializar el servicio de recuperación RAG. "
                        f"Error al crear embeddings automáticamente: {create_error}. "
                        f"Asegúrate de que el archivo CSV existe en '{csv_path}' o usa el endpoint /embeddings/load para cargar embeddings manualmente."
                    )
            
            # Crear el servicio principal RAG
            self._rag_question_service = RAGQuestionService(
                generation_service=rag_generation_service,
                retrieval_service=rag_retrieval_service
            )
        
        return self._rag_question_service
    

    
    async def create_question_service(self, use_rag: bool = True) -> QuestionServicePort:
        """
        Crea el servicio de preguntas RAG
        
        Args:
            use_rag: Parámetro mantenido por compatibilidad (siempre usa RAG)
            
        Returns:
            QuestionServicePort: Servicio de preguntas RAG configurado
        """
        return await self.create_rag_question_service()