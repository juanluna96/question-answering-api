import asyncio
import openai
from typing import List
from ...domain.ports.embedding_service import EmbeddingService

class OpenAIEmbeddingService(EmbeddingService):
    """Adaptador para generar embeddings usando OpenAI"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Inicializa el servicio de OpenAI
        
        Args:
            api_key: Clave de API de OpenAI
            model: Modelo de embedding a usar
        """
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Genera un embedding para un texto
        
        Args:
            text: Texto para generar embedding
            
        Returns:
            Vector de embedding
            
        Raises:
            Exception: Si hay error en la API de OpenAI
        """
        try:
            # Limpiar y preparar el texto
            cleaned_text = self._clean_text(text)
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=cleaned_text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            raise Exception(f"Error al generar embedding: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos en lote
        
        Args:
            texts: Lista de textos para generar embeddings
            
        Returns:
            Lista de vectores de embedding
            
        Raises:
            Exception: Si hay error en la API de OpenAI
        """
        try:
            # Limpiar todos los textos
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            # OpenAI permite hasta 2048 textos por batch, pero usaremos chunks más pequeños
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(cleaned_texts), batch_size):
                batch = cleaned_texts[i:i + batch_size]
                
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Pequeña pausa entre batches para evitar rate limiting
                if i + batch_size < len(cleaned_texts):
                    await asyncio.sleep(0.1)
            
            return all_embeddings
            
        except Exception as e:
            raise Exception(f"Error al generar embeddings en lote: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Limpia y prepara el texto para el embedding
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        # Convertir a string si no lo es
        text = str(text)
        
        # Remover caracteres de control y espacios extra
        text = ' '.join(text.split())
        
        # Limitar longitud (OpenAI tiene límite de tokens)
        # Aproximadamente 8000 tokens = ~32000 caracteres
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        return text
    
    def get_model_info(self) -> dict:
        """Obtiene información del modelo usado
        
        Returns:
            Información del modelo
        """
        return {
            "model": self.model,
            "provider": "OpenAI",
            "max_tokens": 8191,  # Para text-embedding-3-small
            "dimensions": 1536   # Para text-embedding-3-small
        }