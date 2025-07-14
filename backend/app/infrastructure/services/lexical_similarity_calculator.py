import re
import numpy as np
import logging
from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from ...domain.entities.document import DocumentEmbedding

class LexicalSimilarityCalculator:
    """Servicio para calcular similitud lexical usando TF-IDF (Paso 3 de RAG)"""
    
    def __init__(self):
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.document_tfidf_matrix = None
        self.fitted_documents: List[str] = []
    
    async def calculate_query_similarity(
        self, 
        query: str, 
        document_embeddings: List[DocumentEmbedding]
    ) -> List[tuple[DocumentEmbedding, float]]:
        """
        Calcula similitud lexical entre una consulta y documentos usando TF-IDF
        
        Args:
            query: Consulta de búsqueda
            document_embeddings: Lista de embeddings de documentos
            
        Returns:
            Lista de tuplas (DocumentEmbedding, similarity_score)
        """
        if not document_embeddings:
            logging.warning("No hay documentos para calcular similitud lexical")
            return []
        
        logging.info(f"Calculando similitud lexical para {len(document_embeddings)} documentos...")
        
        # Paso 1: Extraer contenido de documentos
        documents_text = [doc.content for doc in document_embeddings]
        
        # Paso 2: Preprocesar textos
        processed_query = self._preprocess_text(query)
        processed_docs = [self._preprocess_text(doc) for doc in documents_text]
        
        logging.debug(f"Textos preprocesados (query: '{processed_query[:50]}...')")
        
        # Paso 3: Calcular similitudes TF-IDF
        similarities = await self._compute_tfidf_similarities(
            processed_query, 
            processed_docs
        )
        
        # Paso 4: Combinar documentos con sus scores
        results = list(zip(document_embeddings, similarities))
        
        logging.info(f"Similitud lexical calculada")
        logging.info(f"Score promedio: {np.mean(similarities):.4f}")
        logging.info(f"Score máximo: {max(similarities):.4f}")
        logging.info(f"Score mínimo: {min(similarities):.4f}")
        
        return results
    
    async def _compute_tfidf_similarities(
        self, 
        query: str, 
        documents: List[str]
    ) -> List[float]:
        """
        Calcula similitudes usando TF-IDF y cosine similarity
        
        Args:
            query: Consulta preprocesada
            documents: Lista de documentos preprocesados
            
        Returns:
            Lista de scores de similitud (0-1)
        """
        try:
            # Crear corpus completo (query + documentos)
            corpus = [query] + documents
            
            # Configurar vectorizador TF-IDF
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,  # Limitar vocabulario
                stop_words='english',  # Remover stop words
                ngram_range=(1, 2),  # Usar unigramas y bigramas
                min_df=1,  # Mínima frecuencia de documento
                max_df=0.95,  # Máxima frecuencia de documento
                lowercase=True,  # Convertir a minúsculas
                token_pattern=r'\b[a-záéíóúñü]{2,}\b'  # Tokens de al menos 2 caracteres
            )
            
            logging.debug(f"Configurando TF-IDF con corpus de {len(corpus)} textos...")
            
            # Ajustar y transformar corpus
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            
            # Separar query y documentos
            query_vec = tfidf_matrix[0:1]  # Primera fila (query)
            doc_matrix = tfidf_matrix[1:]   # Resto de filas (documentos)
            
            # Información de la matriz TF-IDF
            try:
                matrix_shape = getattr(tfidf_matrix, 'shape', 'unknown')
                vocab_size = len(self.tfidf_vectorizer.vocabulary_)
                logging.debug(f"Matriz TF-IDF: {matrix_shape}, Vocabulario: {vocab_size}")
            except Exception:
                logging.debug("Matriz TF-IDF creada exitosamente")
            
            # Calcular similitud coseno
            similarities = cosine_similarity(query_vec, doc_matrix)[0]
            
            # Asegurar que los scores estén en rango [0, 1]
            similarities = np.clip(similarities, 0, 1)
            
            return similarities.tolist()
            
        except ValueError as e:
            logging.warning(f"Error en TF-IDF (vocabulario insuficiente): {e}")
            # Retornar scores uniformes bajos
            return [0.1] * len(documents)
        except Exception as e:
            logging.error(f"Error calculando similitud lexical: {e}")
            # Retornar scores uniformes muy bajos
            return [0.05] * len(documents)
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocesa texto para búsqueda lexical
        
        Args:
            text: Texto a preprocesar
            
        Returns:
            Texto preprocesado
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover caracteres especiales pero mantener espacios y acentos
        text = re.sub(r'[^a-záéíóúñü\s]', ' ', text)
        
        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Remover espacios al inicio y final
        text = text.strip()
        
        return text
    
    async def get_top_similar_documents(
        self, 
        query: str, 
        document_embeddings: List[DocumentEmbedding], 
        top_k: int = 5
    ) -> List[tuple[DocumentEmbedding, float]]:
        """
        Obtiene los documentos más similares lexicalmente
        
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
        
        logging.info(f"Top {len(top_results)} documentos más similares lexicalmente:")
        for i, (doc, score) in enumerate(top_results, 1):
            content_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
            logging.debug(f"  {i}. Score: {score:.4f} - {content_preview}")
        
        return top_results
    
    def get_vocabulary_info(self) -> dict:
        """
        Obtiene información sobre el vocabulario TF-IDF
        
        Returns:
            Diccionario con información del vocabulario
        """
        if not self.tfidf_vectorizer:
            return {"error": "TF-IDF no ha sido ajustado"}
        
        vocab = self.tfidf_vectorizer.vocabulary_
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        
        return {
            "vocabulary_size": len(vocab),
            "max_features": self.tfidf_vectorizer.max_features,
            "ngram_range": self.tfidf_vectorizer.ngram_range,
            "min_df": self.tfidf_vectorizer.min_df,
            "max_df": self.tfidf_vectorizer.max_df,
            "sample_features": feature_names[:10].tolist() if len(feature_names) > 0 else []
        }
    
    def get_similarity_stats(self, similarities: List[float]) -> dict:
        """
        Obtiene estadísticas de similitud lexical
        
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
            "percentile_25": float(np.percentile(similarities_array, 25)),
            "non_zero_count": int(np.count_nonzero(similarities_array))
        }