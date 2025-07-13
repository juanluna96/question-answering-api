from typing import List, Tuple, Dict, Any, Optional
from ...domain.entities.document import DocumentEmbedding

class ContextBuilder:
    """Servicio para construir contexto a partir de documentos recuperados (Paso 1 de Aumento)"""
    
    def __init__(self, separator: str = "\n\n---\n\n"):
        """
        Inicializa el constructor de contexto
        
        Args:
            separator: Separador entre documentos en el contexto
        """
        self.separator = separator
        print(f"🔧 ContextBuilder inicializado con separador: '{separator}'")
    
    async def combine_documents_text(
        self,
        retrieved_documents: List[Tuple[DocumentEmbedding, float, Dict[str, Any]]]
    ) -> str:
        """
        Une los textos de los documentos recuperados para crear el contexto
        
        Args:
            retrieved_documents: Lista de documentos con scores y detalles
            
        Returns:
            Texto combinado de todos los documentos
        """
        if not retrieved_documents:
            print("⚠️ No hay documentos para combinar")
            return ""
        
        print(f"📝 Combinando texto de {len(retrieved_documents)} documentos...")
        
        combined_texts = []
        total_chars = 0
        
        for i, (document, score, details) in enumerate(retrieved_documents, 1):
            # Crear encabezado del documento con información de relevancia
            doc_header = self._create_document_header(i, document, score, details)
            
            # Combinar encabezado y contenido
            doc_text = f"{doc_header}\n{document.content}"
            
            combined_texts.append(doc_text)
            total_chars += len(doc_text)
            
            print(f"  📄 Doc {i}: {len(document.content)} chars (score: {score:.3f})")
        
        # Unir todos los textos con el separador
        final_context = self.separator.join(combined_texts)
        
        print(f"✅ Contexto combinado exitosamente")
        print(f"📊 Total de caracteres: {len(final_context):,}")
        print(f"📊 Número de documentos: {len(retrieved_documents)}")
        print(f"📊 Promedio de caracteres por documento: {total_chars // len(retrieved_documents):,}")
        
        return final_context
    
    def _create_document_header(
        self,
        doc_number: int,
        document: DocumentEmbedding,
        score: float,
        details: Dict[str, Any]
    ) -> str:
        """
        Crea un encabezado informativo para cada documento
        
        Args:
            doc_number: Número del documento en la lista
            document: Documento embedding
            score: Score de relevancia
            details: Detalles adicionales del scoring
            
        Returns:
            Encabezado formateado del documento
        """
        # Información básica
        header_lines = [
            f"[DOCUMENTO {doc_number}]",
            f"ID: {document.document_id}",
            f"Relevancia: {score:.3f}"
        ]
        
        # Agregar detalles de scoring si están disponibles
        if "semantic_score" in details:
            header_lines.append(f"Score Semántico: {details['semantic_score']:.3f}")
        
        if "lexical_score" in details:
            header_lines.append(f"Score Lexical: {details['lexical_score']:.3f}")
        
        # Agregar información del modelo si está disponible
        if hasattr(document, 'model') and document.model:
            header_lines.append(f"Modelo: {document.model}")
        
        # Agregar longitud del contenido
        header_lines.append(f"Longitud: {len(document.content)} caracteres")
        
        return "\n".join(header_lines)
    
    async def combine_documents_with_metadata(
        self,
        retrieved_documents: List[Tuple[DocumentEmbedding, float, Dict[str, Any]]],
        include_scores: bool = True,
        include_ids: bool = False
    ) -> str:
        """
        Une documentos con opciones de metadatos personalizables
        
        Args:
            retrieved_documents: Lista de documentos recuperados
            include_scores: Si incluir scores en el contexto
            include_ids: Si incluir IDs de documentos
            
        Returns:
            Contexto combinado con metadatos opcionales
        """
        if not retrieved_documents:
            return ""
        
        print(f"📝 Combinando {len(retrieved_documents)} documentos con metadatos personalizados...")
        
        combined_texts = []
        
        for i, (document, score, details) in enumerate(retrieved_documents, 1):
            doc_parts = []
            
            # Agregar encabezado si se requieren metadatos
            if include_scores or include_ids:
                header_parts = []
                
                if include_ids:
                    header_parts.append(f"ID: {document.document_id}")
                
                if include_scores:
                    header_parts.append(f"Relevancia: {score:.3f}")
                
                if header_parts:
                    doc_parts.append(f"[{' | '.join(header_parts)}]")
            
            # Agregar contenido del documento
            doc_parts.append(document.content)
            
            # Combinar partes del documento
            doc_text = "\n".join(doc_parts)
            combined_texts.append(doc_text)
        
        final_context = self.separator.join(combined_texts)
        
        print(f"✅ Contexto con metadatos combinado: {len(final_context):,} caracteres")
        
        return final_context
    
    async def get_context_statistics(
        self,
        context: str,
        retrieved_documents: List[Tuple[DocumentEmbedding, float, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas del contexto generado
        
        Args:
            context: Contexto combinado
            retrieved_documents: Documentos originales
            
        Returns:
            Diccionario con estadísticas del contexto
        """
        if not context or not retrieved_documents:
            return {"error": "Contexto o documentos vacíos"}
        
        # Estadísticas básicas
        stats = {
            "total_characters": len(context),
            "total_words": len(context.split()),
            "total_lines": len(context.split('\n')),
            "total_documents": len(retrieved_documents),
            "separator_used": self.separator,
            "separator_count": context.count(self.separator)
        }
        
        # Estadísticas de documentos
        doc_lengths = [len(doc.content) for doc, _, _ in retrieved_documents]
        doc_scores = [score for _, score, _ in retrieved_documents]
        
        stats.update({
            "documents": {
                "avg_length": sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0,
                "min_length": min(doc_lengths) if doc_lengths else 0,
                "max_length": max(doc_lengths) if doc_lengths else 0,
                "avg_score": sum(doc_scores) / len(doc_scores) if doc_scores else 0,
                "min_score": min(doc_scores) if doc_scores else 0,
                "max_score": max(doc_scores) if doc_scores else 0
            }
        })
        
        # Estimación de tokens (aproximada: 1 token ≈ 4 caracteres)
        estimated_tokens = len(context) // 4
        stats["estimated_tokens"] = estimated_tokens
        
        return stats
    
    def update_separator(self, new_separator: str):
        """
        Actualiza el separador entre documentos
        
        Args:
            new_separator: Nuevo separador a usar
        """
        old_separator = self.separator
        self.separator = new_separator
        print(f"🔄 Separador actualizado: '{old_separator}' → '{new_separator}'")
    
    def get_configuration(self) -> Dict[str, str]:
        """
        Obtiene la configuración actual del constructor
        
        Returns:
            Diccionario con la configuración
        """
        return {
            "separator": self.separator,
            "separator_length": str(len(self.separator)),
            "separator_preview": repr(self.separator)
        }