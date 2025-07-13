"""Configuración de la aplicación"""

import os
from typing import Optional
from dotenv import load_dotenv

class Settings:
    """Clase de configuración para la aplicación RAG"""
    
    def __init__(self):
        """Inicializa la configuración cargando variables de entorno"""
        # Cargar variables de entorno desde .env
        load_dotenv(override=True)
        
        # Configuración de OpenAI
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
        # Configuración de generación
        self.max_tokens: int = int(os.getenv("MAX_TOKENS", "1000"))
        self.temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Configuración de caché y archivos
        self.embedding_cache_path: str = os.getenv(
            "DEFAULT_CACHE_PATH", 
            "./data/cache/embeddings.pkl"
        )
        self.documents_csv_path: str = os.getenv(
            "DOCUMENTS_CSV_PATH", 
            "./data/documents.csv"
        )
        self.max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
        self.batch_size: int = int(os.getenv("BATCH_SIZE", "100"))
        
        # Configuración RAG
        self.enable_rag: bool = os.getenv("ENABLE_RAG", "true").lower() == "true"
        self.max_retrieved_documents: int = int(os.getenv("MAX_RETRIEVED_DOCUMENTS", "5"))
        self.similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
        
        # Configuración de timeouts
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
    def validate(self) -> bool:
        """Valida que la configuración sea correcta
        
        Returns:
            bool: True si la configuración es válida
            
        Raises:
            ValueError: Si alguna configuración es inválida
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY es requerida")
            
        if self.max_tokens <= 0:
            raise ValueError("MAX_TOKENS debe ser mayor a 0")
            
        if not 0 <= self.temperature <= 2:
            raise ValueError("TEMPERATURE debe estar entre 0 y 2")
            
        if self.max_file_size_mb <= 0:
            raise ValueError("MAX_FILE_SIZE_MB debe ser mayor a 0")
            
        if self.batch_size <= 0:
            raise ValueError("BATCH_SIZE debe ser mayor a 0")
            
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("SIMILARITY_THRESHOLD debe estar entre 0 y 1")
            
        return True
    
    def get_config_dict(self) -> dict:
        """Obtiene la configuración como diccionario
        
        Returns:
            dict: Configuración completa
        """
        return {
            "openai_api_key": "***" if self.openai_api_key else None,  # Ocultar API key
            "openai_model": self.openai_model,
            "embedding_model": self.embedding_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "embedding_cache_path": self.embedding_cache_path,
            "documents_csv_path": self.documents_csv_path,
            "max_file_size_mb": self.max_file_size_mb,
            "batch_size": self.batch_size,
            "enable_rag": self.enable_rag,
            "max_retrieved_documents": self.max_retrieved_documents,
            "similarity_threshold": self.similarity_threshold,
            "request_timeout": self.request_timeout
        }