import numpy as np
import logging
from typing import List, Tuple, Dict, Optional, Any
from ...domain.entities.document import DocumentEmbedding

class ScoreCombiner:
    """Servicio para combinar scores semánticos y lexicales (Paso 4 de RAG)"""
    
    def __init__(self, semantic_weight: float = 0.7, lexical_weight: float = 0.3):
        self.logger = logging.getLogger(__name__)
        """
        Inicializa el combinador de scores
        
        Args:
            semantic_weight: Peso para similitud semántica (0.0-1.0)
            lexical_weight: Peso para similitud lexical (0.0-1.0)
        """
        if abs(semantic_weight + lexical_weight - 1.0) > 0.001:
            raise ValueError("Los pesos deben sumar 1.0")
        
        self.semantic_weight = semantic_weight
        self.lexical_weight = lexical_weight
        
        self.logger.info(f"🔧 ScoreCombiner configurado: semántico={semantic_weight}, lexical={lexical_weight}")
    
    async def combine_similarity_scores(
        self,
        semantic_results: List[Tuple[DocumentEmbedding, float]],
        lexical_results: List[Tuple[DocumentEmbedding, float]]
    ) -> List[Tuple[DocumentEmbedding, float, Dict[str, float]]]:
        """
        Combina scores semánticos y lexicales
        
        Args:
            semantic_results: Lista de (DocumentEmbedding, semantic_score)
            lexical_results: Lista de (DocumentEmbedding, lexical_score)
            
        Returns:
            Lista de (DocumentEmbedding, combined_score, score_details)
        """
        if len(semantic_results) != len(lexical_results):
            raise ValueError("Las listas de resultados deben tener la misma longitud")
        
        self.logger.info(f"🔄 Combinando {len(semantic_results)} scores semánticos y lexicales...")
        
        # Crear mapeo de document_id a scores para facilitar la combinación
        semantic_map = {doc.document_id: score for doc, score in semantic_results}
        lexical_map = {doc.document_id: score for doc, score in lexical_results}
        
        combined_results = []
        
        for doc, semantic_score in semantic_results:
            doc_id = doc.document_id
            lexical_score = lexical_map.get(doc_id, 0.0)
            
            # Calcular score combinado
            combined_score = (
                self.semantic_weight * semantic_score + 
                self.lexical_weight * lexical_score
            )
            
            # Detalles de scores para debugging
            score_details = {
                "semantic_score": semantic_score,
                "lexical_score": lexical_score,
                "combined_score": combined_score,
                "semantic_weight": self.semantic_weight,
                "lexical_weight": self.lexical_weight
            }
            
            combined_results.append((doc, combined_score, score_details))
        
        # Ordenar por score combinado descendente
        combined_results.sort(key=lambda x: x[1], reverse=True)
        
        self.logger.info(f"✅ Scores combinados exitosamente")
        self._log_combination_stats(combined_results)
        
        return combined_results
    
    async def get_top_documents(
        self,
        semantic_results: List[Tuple[DocumentEmbedding, float]],
        lexical_results: List[Tuple[DocumentEmbedding, float]],
        top_k: int = 5
    ) -> List[Tuple[DocumentEmbedding, float, Dict[str, float]]]:
        """
        Obtiene los top_k documentos más relevantes después de combinar scores
        
        Args:
            semantic_results: Resultados de similitud semántica
            lexical_results: Resultados de similitud lexical
            top_k: Número de documentos más relevantes
            
        Returns:
            Lista de top_k documentos con scores combinados
        """
        combined_results = await self.combine_similarity_scores(
            semantic_results, lexical_results
        )
        
        top_results = combined_results[:top_k]
        
        self.logger.info(f"🏆 Top {len(top_results)} documentos más relevantes:")
        for i, (document, combined_score, details) in enumerate(top_results, 1):
            content_preview = document.content[:100] + "..." if len(document.content) > 100 else document.content
            self.logger.info(f"  {i}. Score: {combined_score:.4f} (S:{details['semantic_score']:.3f}, L:{details['lexical_score']:.3f}) - {content_preview}")
        
        return top_results
    
    def _log_combination_stats(self, combined_results: List[Tuple[DocumentEmbedding, float, Dict[str, float]]]):
        """
        Registra estadísticas de la combinación de scores
        """
        if not combined_results:
            return
        
        combined_scores = [score for _, score, _ in combined_results]
        semantic_scores = [details['semantic_score'] for _, _, details in combined_results]
        lexical_scores = [details['lexical_score'] for _, _, details in combined_results]
        
        self.logger.info(f"📊 Estadísticas de combinación:")
        self.logger.info(f"   Combined - Promedio: {np.mean(combined_scores):.4f}, Max: {max(combined_scores):.4f}, Min: {min(combined_scores):.4f}")
        self.logger.info(f"   Semantic - Promedio: {np.mean(semantic_scores):.4f}, Max: {max(semantic_scores):.4f}, Min: {min(semantic_scores):.4f}")
        self.logger.info(f"   Lexical  - Promedio: {np.mean(lexical_scores):.4f}, Max: {max(lexical_scores):.4f}, Min: {min(lexical_scores):.4f}")
    
    async def analyze_score_distribution(
        self,
        combined_results: List[Tuple[DocumentEmbedding, float, Dict[str, float]]]
    ) -> Dict[str, Any]:
        """
        Analiza la distribución de scores combinados
        
        Args:
            combined_results: Resultados con scores combinados
            
        Returns:
            Diccionario con análisis estadístico
        """
        if not combined_results:
            return {"error": "No hay resultados para analizar"}
        
        combined_scores = np.array([score for _, score, _ in combined_results])
        semantic_scores = np.array([details['semantic_score'] for _, _, details in combined_results])
        lexical_scores = np.array([details['lexical_score'] for _, _, details in combined_results])
        
        analysis = {
            "total_documents": len(combined_results),
            "weights": {
                "semantic": self.semantic_weight,
                "lexical": self.lexical_weight
            },
            "combined_scores": {
                "mean": float(np.mean(combined_scores)),
                "std": float(np.std(combined_scores)),
                "min": float(np.min(combined_scores)),
                "max": float(np.max(combined_scores)),
                "median": float(np.median(combined_scores)),
                "percentile_75": float(np.percentile(combined_scores, 75)),
                "percentile_25": float(np.percentile(combined_scores, 25))
            },
            "semantic_scores": {
                "mean": float(np.mean(semantic_scores)),
                "std": float(np.std(semantic_scores)),
                "min": float(np.min(semantic_scores)),
                "max": float(np.max(semantic_scores))
            },
            "lexical_scores": {
                "mean": float(np.mean(lexical_scores)),
                "std": float(np.std(lexical_scores)),
                "min": float(np.min(lexical_scores)),
                "max": float(np.max(lexical_scores))
            },
            "correlation": {
                "semantic_lexical": float(np.corrcoef(semantic_scores, lexical_scores)[0, 1]) if len(semantic_scores) > 1 else 0.0
            }
        }
        
        return analysis
    
    def update_weights(self, semantic_weight: float, lexical_weight: float):
        """
        Actualiza los pesos de combinación
        
        Args:
            semantic_weight: Nuevo peso semántico
            lexical_weight: Nuevo peso lexical
        """
        if abs(semantic_weight + lexical_weight - 1.0) > 0.001:
            raise ValueError("Los pesos deben sumar 1.0")
        
        old_semantic = self.semantic_weight
        old_lexical = self.lexical_weight
        
        self.semantic_weight = semantic_weight
        self.lexical_weight = lexical_weight
        
        self.logger.info(f"🔄 Pesos actualizados: ({old_semantic:.2f}, {old_lexical:.2f}) → ({semantic_weight:.2f}, {lexical_weight:.2f})")
    
    def get_configuration(self) -> Dict[str, float]:
        """
        Obtiene la configuración actual del combinador
        
        Returns:
            Diccionario con la configuración actual
        """
        return {
            "semantic_weight": self.semantic_weight,
            "lexical_weight": self.lexical_weight,
            "total_weight": self.semantic_weight + self.lexical_weight
        }