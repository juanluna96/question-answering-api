import logging
import sys
from typing import Optional
from pathlib import Path


class LoggingConfig:
    """Configuración centralizada de logging para la aplicación"""
    
    @staticmethod
    def setup_logging(
        level: str = "INFO",
        log_file: Optional[str] = None,
        format_string: Optional[str] = None
    ) -> None:
        """
        Configura el sistema de logging de la aplicación
        
        Args:
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Archivo donde guardar los logs (opcional)
            format_string: Formato personalizado de los logs
        """
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Configurar el logger raíz
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=format_string,
            handlers=[]
        )
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = logging.Formatter(format_string)
        console_handler.setFormatter(console_formatter)
        
        # Handler para archivo (si se especifica)
        handlers = [console_handler]
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_formatter = logging.Formatter(format_string)
            file_handler.setFormatter(file_formatter)
            handlers.append(file_handler)
        
        # Configurar el logger raíz con los handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        for handler in handlers:
            root_logger.addHandler(handler)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Obtiene un logger con el nombre especificado
        
        Args:
            name: Nombre del logger (generalmente __name__)
            
        Returns:
            Logger configurado
        """
        return logging.getLogger(name)
    
    @staticmethod
    def setup_rag_logging() -> None:
        """
        Configuración específica para los servicios RAG con emojis y colores
        """
        # Formato especial para RAG con emojis
        rag_format = "%(asctime)s - 🤖 %(name)s - %(levelname)s - %(message)s"
        
        # Configurar logging para servicios RAG
        rag_services = [
            'app.infrastructure.services.rag_generation_service',
            'app.infrastructure.services.rag_retrieval_service',
            'app.infrastructure.services.rag_question_service',
            'app.infrastructure.services.openai_generation_service',
            'app.infrastructure.services.context_builder',
            'app.infrastructure.services.prompt_builder',
            'app.infrastructure.services.semantic_similarity_calculator',
            'app.infrastructure.services.lexical_similarity_calculator',
            'app.infrastructure.services.score_combiner',
            'app.infrastructure.services.context_limiter',
            'app.infrastructure.services.embedding_cache_reader',
            'app.domain.services.embedding_manager',
            'app.application.services.question_service_factory'
        ]
        
        for service_name in rag_services:
            logger = logging.getLogger(service_name)
            logger.setLevel(logging.INFO)