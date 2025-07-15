import numpy as np
from typing import List, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import logging

from ...domain.entities.document import DocumentEmbedding
from ...domain.ports.embedding_service import EmbeddingService

class SemanticSimilarityCalculator:
    """Servicio para calcular similitud semántica (Paso 2 de RAG)"""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
    
    async def calculate_query_similarity(
        self, 
        query: str, 
        document_embeddings: List[DocumentEmbedding]
    ) -> List[tuple[DocumentEmbedding, float]]:
        """
        Calcula similitud semántica entre una consulta y documentos
        
        Args:
            query: Consulta de búsqueda
            document_embeddings: Lista de embeddings de documentos
            
        Returns:
            Lista de tuplas (DocumentEmbedding, similarity_score)
        """
        if not document_embeddings:
            logging.warning("No hay documentos para calcular similitud")
            return []
        
        logging.info(f"🔍 Calculando similitud semántica para {len(document_embeddings)} documentos...")
        
        # Paso 1: Generar embedding de la consulta
        query_embedding = await self.embedding_service.generate_embedding(query)
        logging.debug(f"📊 Embedding de consulta generado (dimensión: {len(query_embedding)})")
        
        # Paso 2: Extraer embeddings de documentos
        doc_embeddings_matrix = [doc.embedding for doc in document_embeddings]
        
        # Paso 3: Calcular similitudes
        similarities = await self._compute_cosine_similarities(
            query_embedding, 
            doc_embeddings_matrix
        )
        
        # Paso 4: Combinar documentos con sus scores
        results = list(zip(document_embeddings, similarities))
        
        logging.info(f"✅ Similitud semántica calculada")
        logging.info(f"📈 Score promedio: {np.mean(similarities):.4f}")
        logging.info(f"📈 Score máximo: {max(similarities):.4f}")
        logging.info(f"📈 Score mínimo: {min(similarities):.4f}")
        
        return results
    
    async def _compute_cosine_similarities(
        self, 
        query_embedding: List[float], 
        document_embeddings: List[List[float]]
    ) -> List[float]:
        """
        Calcula similitud coseno entre query y documentos
        
        Args:
            query_embedding: Embedding de la consulta
            document_embeddings: Lista de embeddings de documentos
            
        Returns:
            Lista de scores de similitud (0-1)
        """
        try:
            # Convertir a arrays numpy
            query_vec = np.array(query_embedding).reshape(1, -1)
            doc_matrix = np.array(document_embeddings)
            
            # Validar dimensiones
            if query_vec.shape[1] != doc_matrix.shape[1]:
                raise ValueError(
                    f"Dimensiones incompatibles: query={query_vec.shape[1]}, "
                    f"docs={doc_matrix.shape[1]}"
                )
            
            # Calcular cosine similarity
            similarities = cosine_similarity(query_vec, doc_matrix)[0]
            
            # Normalizar scores a rango [0, 1]
            # cosine_similarity retorna valores entre -1 y 1
            normalized_scores = (similarities + 1) / 2
            
            return normalized_scores.tolist()
            
        except Exception as e:
            logging.error(f"❌ Error calculando similitud semántica: {e}")
            # Retornar scores uniformes en caso de error
            return [0.1] * len(document_embeddings)
    
    async def get_top_similar_documents(
        self, 
        query: str, 
        document_embeddings: List[DocumentEmbedding], 
        top_k: int = 5
    ) -> List[tuple[DocumentEmbedding, float]]:
        """
        Obtiene los documentos más similares semánticamente
        
        Args:
            query: Consulta de búsqueda
            document_embeddings: Lista de embeddings de documentos
            top_k: Número de documentos más relevantes
            
        Returns:
            Lista ordenada de tuplas (DocumentEmbedding, similarity_score)
        """
        # Calcular similitudes
        similarities = await self.calculate_query_similarity(query, document_embeddings)
        
        # Ordenar por score descendente
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar top_k
        top_results = similarities[:top_k]
        
        logging.info(f"🏆 Top {len(top_results)} documentos más similares:")
        for i, (doc, score) in enumerate(top_results, 1):
            content_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
            logging.debug(f"  {i}. Score: {score:.4f} - {content_preview}")
        
        return top_results
    
    def get_similarity_stats(self, similarities: List[float]) -> dict:
        """
        Obtiene estadísticas de similitud
        
        Args:
            similarities: Lista de scores de similitud
            
        Returns:
            Diccionario con estadísticas
        """
        if not similarities:
            return {"error": "No hay similitudes para analizar"}
        
        similarities_array = np.array(similarities)
        
        return {
            "count": len(similarities),
            "mean": float(np.mean(similarities_array)),
            "std": float(np.std(similarities_array)),
            "min": float(np.min(similarities_array)),
            "max": float(np.max(similarities_array)),
            "median": float(np.median(similarities_array)),
            "percentile_75": float(np.percentile(similarities_array, 75)),
            "percentile_25": float(np.percentile(similarities_array, 25))
        }