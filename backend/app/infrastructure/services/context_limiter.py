from typing import List, Tuple, Dict, Any, Optional
from ...domain.entities.document import DocumentEmbedding

class ContextLimiter:
    """Servicio para limitar la longitud del contexto (Paso 2 de Aumento)"""
    
    def __init__(
        self,
        max_tokens: int = 4000,
        chars_per_token: float = 4.0,
        preserve_strategy: str = "top_scores"
    ):
        """
        Inicializa el limitador de contexto
        
        Args:
            max_tokens: Máximo número de tokens permitidos
            chars_per_token: Estimación de caracteres por token
            preserve_strategy: Estrategia de preservación ('top_scores', 'balanced', 'first_n')
        """
        self.max_tokens = max_tokens
        self.chars_per_token = chars_per_token
        self.max_chars = int(max_tokens * chars_per_token)
        self.preserve_strategy = preserve_strategy
        
        print(f"🔧 ContextLimiter inicializado:")
        print(f"   📊 Máximo tokens: {max_tokens:,}")
        print(f"   📊 Máximo caracteres: {self.max_chars:,}")
        print(f"   🎯 Estrategia: {preserve_strategy}")
    
    async def limit_context_length(
        self,
        context: str,
        retrieved_documents: List[Tuple[DocumentEmbedding, float, Dict[str, Any]]],
        separator: str = "\n\n---\n\n"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Limita la longitud del contexto según los límites configurados
        
        Args:
            context: Contexto original combinado
            retrieved_documents: Documentos originales con scores
            separator: Separador usado entre documentos
            
        Returns:
            Tupla con (contexto_limitado, estadísticas_limitación)
        """
        print(f"📏 Limitando contexto de {len(context):,} caracteres...")
        
        # Verificar si el contexto ya está dentro de los límites
        if len(context) <= self.max_chars:
            print(f"✅ Contexto dentro de límites: {len(context):,} ≤ {self.max_chars:,}")
            return context, {
                "limited": False,
                "original_length": len(context),
                "final_length": len(context),
                "documents_kept": len(retrieved_documents),
                "documents_removed": 0,
                "strategy_used": "none"
            }
        
        print(f"⚠️ Contexto excede límites: {len(context):,} > {self.max_chars:,}")
        print(f"🔄 Aplicando estrategia: {self.preserve_strategy}")
        
        # Aplicar estrategia de limitación
        if self.preserve_strategy == "top_scores":
            limited_context, stats = await self._limit_by_top_scores(
                retrieved_documents, separator
            )
        elif self.preserve_strategy == "balanced":
            limited_context, stats = await self._limit_by_balanced_approach(
                retrieved_documents, separator
            )
        elif self.preserve_strategy == "first_n":
            limited_context, stats = await self._limit_by_first_n(
                retrieved_documents, separator
            )
        else:
            # Fallback a top_scores
            print(f"⚠️ Estrategia desconocida '{self.preserve_strategy}', usando 'top_scores'")
            limited_context, stats = await self._limit_by_top_scores(
                retrieved_documents, separator
            )
        
        # Agregar información general a las estadísticas
        stats.update({
            "limited": True,
            "original_length": len(context),
            "final_length": len(limited_context),
            "reduction_percentage": ((len(context) - len(limited_context)) / len(context)) * 100,
            "strategy_used": self.preserve_strategy
        })
        
        print(f"✅ Contexto limitado exitosamente:")
        print(f"   📊 Longitud original: {len(context):,} caracteres")
        print(f"   📊 Longitud final: {len(limited_context):,} caracteres")
        print(f"   📊 Reducción: {stats['reduction_percentage']:.1f}%")
        print(f"   📊 Documentos conservados: {stats['documents_kept']}/{len(retrieved_documents)}")
        
        return limited_context, stats
    
    async def _limit_by_top_scores(
        self,
        retrieved_documents: List[Tuple[DocumentEmbedding, float, Dict[str, Any]]],
        separator: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Limita el contexto preservando documentos con mejores scores
        """
        print("🏆 Aplicando estrategia: Top Scores")
        
        # Los documentos ya vienen ordenados por score (descendente)
        selected_docs = []
        current_length = 0
        separator_length = len(separator)
        
        for i, (document, score, details) in enumerate(retrieved_documents):
            # Calcular longitud del documento con encabezado
            doc_header = self._create_simple_header(i + 1, document, score)
            doc_text = f"{doc_header}\n{document.content}"
            doc_length = len(doc_text)
            
            # Verificar si agregar este documento excedería el límite
            additional_length = doc_length
            if selected_docs:  # Agregar separador si no es el primer documento
                additional_length += separator_length
            
            if current_length + additional_length <= self.max_chars:
                selected_docs.append((document, score, details))
                current_length += additional_length
                print(f"  ✅ Doc {i+1} incluido (score: {score:.3f}, chars: {doc_length:,})")
            else:
                print(f"  ❌ Doc {i+1} excluido (score: {score:.3f}, chars: {doc_length:,})")
                break
        
        # Construir contexto final
        final_texts = []
        for i, (document, score, details) in enumerate(selected_docs):
            doc_header = self._create_simple_header(i + 1, document, score)
            doc_text = f"{doc_header}\n{document.content}"
            final_texts.append(doc_text)
        
        final_context = separator.join(final_texts)
        
        return final_context, {
            "documents_kept": len(selected_docs),
            "documents_removed": len(retrieved_documents) - len(selected_docs),
            "avg_score_kept": sum(score for _, score, _ in selected_docs) / len(selected_docs) if selected_docs else 0
        }
    
    async def _limit_by_balanced_approach(
        self,
        retrieved_documents: List[Tuple[DocumentEmbedding, float, Dict[str, Any]]],
        separator: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Limita el contexto con un enfoque balanceado (trunca documentos largos)
        """
        print("⚖️ Aplicando estrategia: Balanced")
        
        selected_docs = []
        current_length = 0
        separator_length = len(separator)
        
        # Calcular longitud promedio disponible por documento
        available_space = self.max_chars
        estimated_docs = min(len(retrieved_documents), 5)  # Máximo 5 documentos
        avg_space_per_doc = available_space // estimated_docs
        
        print(f"  📊 Espacio promedio por documento: {avg_space_per_doc:,} caracteres")
        
        for i, (document, score, details) in enumerate(retrieved_documents[:estimated_docs]):
            # Crear encabezado
            doc_header = self._create_simple_header(i + 1, document, score)
            header_length = len(doc_header) + 1  # +1 para el \n
            
            # Calcular espacio disponible para contenido
            available_for_content = avg_space_per_doc - header_length
            if i > 0:  # Restar separador si no es el primer documento
                available_for_content -= separator_length
            
            # Truncar contenido si es necesario
            content = document.content
            if len(content) > available_for_content:
                content = content[:available_for_content - 3] + "..."
                print(f"  ✂️ Doc {i+1} truncado: {len(document.content):,} → {len(content):,} chars")
            else:
                print(f"  ✅ Doc {i+1} completo: {len(content):,} chars")
            
            # Crear documento modificado
            modified_doc = DocumentEmbedding(
                document_id=document.document_id,
                content=content,
                embedding=document.embedding,
                model=getattr(document, 'model', '') or ''
            )
            
            selected_docs.append((modified_doc, score, details))
        
        # Construir contexto final
        final_texts = []
        for i, (document, score, details) in enumerate(selected_docs):
            doc_header = self._create_simple_header(i + 1, document, score)
            doc_text = f"{doc_header}\n{document.content}"
            final_texts.append(doc_text)
        
        final_context = separator.join(final_texts)
        
        # Contar documentos truncados
        documents_truncated = 0
        for i, (selected_doc, _, _) in enumerate(selected_docs):
            if i < len(retrieved_documents):
                original_doc, _, _ = retrieved_documents[i]
                if len(selected_doc.content) < len(original_doc.content):
                    documents_truncated += 1
        
        return final_context, {
            "documents_kept": len(selected_docs),
            "documents_removed": len(retrieved_documents) - len(selected_docs),
            "documents_truncated": documents_truncated
        }
    
    async def _limit_by_first_n(
        self,
        retrieved_documents: List[Tuple[DocumentEmbedding, float, Dict[str, Any]]],
        separator: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Limita el contexto tomando los primeros N documentos que quepan
        """
        print("🔢 Aplicando estrategia: First N")
        
        selected_docs = []
        current_length = 0
        separator_length = len(separator)
        
        for i, (document, score, details) in enumerate(retrieved_documents):
            doc_header = self._create_simple_header(i + 1, document, score)
            doc_text = f"{doc_header}\n{document.content}"
            doc_length = len(doc_text)
            
            additional_length = doc_length
            if selected_docs:
                additional_length += separator_length
            
            if current_length + additional_length <= self.max_chars:
                selected_docs.append((document, score, details))
                current_length += additional_length
                print(f"  ✅ Doc {i+1} incluido (posición: {i+1}, chars: {doc_length:,})")
            else:
                print(f"  ❌ Doc {i+1} excluido (posición: {i+1}, chars: {doc_length:,})")
                break
        
        # Construir contexto final
        final_texts = []
        for i, (document, score, details) in enumerate(selected_docs):
            doc_header = self._create_simple_header(i + 1, document, score)
            doc_text = f"{doc_header}\n{document.content}"
            final_texts.append(doc_text)
        
        final_context = separator.join(final_texts)
        
        return final_context, {
            "documents_kept": len(selected_docs),
            "documents_removed": len(retrieved_documents) - len(selected_docs),
            "selection_method": "sequential"
        }
    
    def _create_simple_header(
        self,
        doc_number: int,
        document: DocumentEmbedding,
        score: float
    ) -> str:
        """
        Crea un encabezado simple para documentos limitados
        """
        return f"[DOCUMENTO {doc_number} - Relevancia: {score:.3f}]"
    
    async def estimate_tokens(self, text: str) -> int:
        """
        Estima el número de tokens en un texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Número estimado de tokens
        """
        return int(len(text) / self.chars_per_token)
    
    async def check_context_limits(
        self,
        context: str
    ) -> Dict[str, Any]:
        """
        Verifica si un contexto está dentro de los límites
        
        Args:
            context: Contexto a verificar
            
        Returns:
            Información sobre límites del contexto
        """
        char_count = len(context)
        estimated_tokens = await self.estimate_tokens(context)
        
        return {
            "character_count": char_count,
            "estimated_tokens": estimated_tokens,
            "within_char_limit": char_count <= self.max_chars,
            "within_token_limit": estimated_tokens <= self.max_tokens,
            "char_usage_percentage": (char_count / self.max_chars) * 100,
            "token_usage_percentage": (estimated_tokens / self.max_tokens) * 100,
            "chars_remaining": max(0, self.max_chars - char_count),
            "tokens_remaining": max(0, self.max_tokens - estimated_tokens)
        }
    
    def update_limits(
        self,
        max_tokens: Optional[int] = None,
        chars_per_token: Optional[float] = None,
        preserve_strategy: Optional[str] = None
    ):
        """
        Actualiza los límites y configuración del limitador
        
        Args:
            max_tokens: Nuevo límite de tokens
            chars_per_token: Nueva estimación de caracteres por token
            preserve_strategy: Nueva estrategia de preservación
        """
        if max_tokens is not None:
            old_tokens = self.max_tokens
            self.max_tokens = max_tokens
            self.max_chars = int(max_tokens * self.chars_per_token)
            print(f"🔄 Límite de tokens actualizado: {old_tokens:,} → {max_tokens:,}")
        
        if chars_per_token is not None:
            old_ratio = self.chars_per_token
            self.chars_per_token = chars_per_token
            self.max_chars = int(self.max_tokens * chars_per_token)
            print(f"🔄 Ratio chars/token actualizado: {old_ratio} → {chars_per_token}")
        
        if preserve_strategy is not None:
            old_strategy = self.preserve_strategy
            self.preserve_strategy = preserve_strategy
            print(f"🔄 Estrategia actualizada: '{old_strategy}' → '{preserve_strategy}'")
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual del limitador
        
        Returns:
            Diccionario con la configuración
        """
        return {
            "max_tokens": self.max_tokens,
            "max_chars": self.max_chars,
            "chars_per_token": self.chars_per_token,
            "preserve_strategy": self.preserve_strategy,
            "available_strategies": ["top_scores", "balanced", "first_n"]
        }