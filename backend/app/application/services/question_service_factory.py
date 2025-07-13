from typing import Optional
from ...domain.ports.question_service_port import QuestionServicePort
from ...infrastructure.services.rag_question_service import RAGQuestionService
from ...infrastructure.services.simple_question_service import SimpleQuestionService
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
        self._simple_question_service: Optional[SimpleQuestionService] = None
    
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
            
            # Crear servicio de generación RAG
            rag_generation_service = RAGGenerationService(
                openai_service=openai_generation
            )
            
            # Crear servicio de recuperación RAG
            rag_retrieval_service = RAGRetrievalService(
                embedding_service=openai_embedding,
                cache_service=cache_service
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
    
    def create_simple_question_service(self) -> SimpleQuestionService:
        """
        Crea una instancia del servicio simple de preguntas (para testing/fallback)
        
        Returns:
            SimpleQuestionService: Servicio simple configurado
        """
        if self._simple_question_service is None:
            self._simple_question_service = SimpleQuestionService()
        
        return self._simple_question_service
    
    async def create_question_service(self, use_rag: bool = True) -> QuestionServicePort:
        """
        Crea el servicio de preguntas apropiado según la configuración
        
        Args:
            use_rag: Si usar el servicio RAG (True) o el simple (False)
            
        Returns:
            QuestionServicePort: Servicio de preguntas configurado
        """
        if use_rag and self._settings.enable_rag:
            return await self.create_rag_question_service()
        else:
            return self.create_simple_question_service()
    
    def get_service_info(self) -> dict:
        """
        Obtiene información sobre los servicios disponibles
        
        Returns:
            dict: Información de configuración
        """
        return {
            'rag_enabled': self._settings.enable_rag,
            'openai_model': self._settings.openai_model,
            'embedding_model': self._settings.embedding_model,
            'max_tokens': self._settings.max_tokens,
            'temperature': self._settings.temperature,
            'cache_path': self._settings.embedding_cache_path,
            'services_initialized': {
                'rag_service': self._rag_question_service is not None,
                'simple_service': self._simple_question_service is not None
            }
        }
    
    async def health_check(self) -> dict:
        """
        Verifica el estado de salud de los servicios
        
        Returns:
            dict: Estado de salud de los servicios
        """
        health_status = {
            'factory_status': 'healthy',
            'services': {}
        }
        
        try:
            # Verificar servicio RAG si está habilitado
            if self._settings.enable_rag:
                if self._rag_question_service:
                    # Verificar que el servicio puede procesar una pregunta simple
                    test_result = await self._rag_question_service.validate_question("test")
                    health_status['services']['rag_service'] = {
                        'status': 'healthy' if test_result else 'warning',
                        'message': 'Service responding' if test_result else 'Validation issues'
                    }
                else:
                    health_status['services']['rag_service'] = {
                        'status': 'not_initialized',
                        'message': 'Service not created yet'
                    }
            
            # Verificar servicio simple
            if self._simple_question_service:
                test_result = await self._simple_question_service.validate_question("test")
                health_status['services']['simple_service'] = {
                    'status': 'healthy' if test_result else 'warning',
                    'message': 'Service responding' if test_result else 'Validation issues'
                }
            
        except Exception as e:
            health_status['factory_status'] = 'error'
            health_status['error'] = str(e)
        
        return health_status
    
    def cleanup(self):
        """
        Limpia los recursos de los servicios
        """
        # Reset de las instancias para forzar recreación
        self._rag_question_service = None
        self._simple_question_service = None