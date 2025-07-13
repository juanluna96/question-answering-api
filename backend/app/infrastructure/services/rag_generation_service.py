from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from .openai_generation_service import OpenAIGenerationService
from .prompt_builder import PromptBuilder
from ...domain.entities.document import Document

class RAGGenerationService:
    """Servicio integrador para generación RAG (Paso 1.2 - Envío de prompt con contexto)"""
    
    def __init__(
        self,
        openai_service: Optional[OpenAIGenerationService] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        default_model: str = "gpt-4o-mini",
        default_max_tokens: int = 1000,
        default_temperature: float = 0.1
    ):
        """
        Inicializa el servicio de generación RAG
        
        Args:
            openai_service: Servicio OpenAI configurado (opcional)
            prompt_builder: Constructor de prompts (opcional)
            default_model: Modelo por defecto
            default_max_tokens: Tokens máximos por defecto
            default_temperature: Temperatura por defecto
        """
        # Inicializar servicios
        self.openai_service = openai_service or OpenAIGenerationService(
            model=default_model,
            max_tokens=default_max_tokens,
            temperature=default_temperature
        )
        
        self.prompt_builder = prompt_builder or PromptBuilder()
        
        # Estadísticas del servicio RAG
        self.rag_stats: Dict[str, Any] = {
            "total_rag_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_documents_processed": 0,
            "average_context_length": 0,
            "average_response_time": 0
        }
        
        print(f"🔗 RAGGenerationService inicializado:")
        print(f"   🤖 Modelo: {self.openai_service.model}")
        print(f"   📊 Max tokens: {self.openai_service.max_tokens}")
        print(f"   🌡️ Temperature: {self.openai_service.temperature}")
    
    async def generate_answer(
        self,
        question: str,
        retrieved_documents: List[Document],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        custom_instructions: Optional[str] = None,
        custom_max_tokens: Optional[int] = None,
        custom_temperature: Optional[float] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Genera una respuesta usando RAG (Paso 1.2 completado)
        
        Args:
            question: Pregunta del usuario
            retrieved_documents: Documentos recuperados del sistema RAG
            conversation_history: Historial de conversación (opcional)
            custom_instructions: Instrucciones personalizadas (opcional)
            custom_max_tokens: Límite personalizado de tokens
            custom_temperature: Temperatura personalizada
            include_metadata: Si incluir metadatos en la respuesta
            
        Returns:
            Diccionario con respuesta y metadatos completos
        """
        print(f"🚀 Iniciando generación RAG...")
        print(f"   ❓ Pregunta: {question[:100]}{'...' if len(question) > 100 else ''}")
        print(f"   📚 Documentos: {len(retrieved_documents)}")
        
        start_time = datetime.now()
        
        try:
            # Actualizar estadísticas
            self.rag_stats["total_rag_requests"] += 1
            self.rag_stats["total_documents_processed"] += len(retrieved_documents)
            
            # Paso 1.2a: Construir prompt con contexto
            print("📝 Construyendo prompt con contexto...")
            
            # Primero necesitamos construir el contexto de los documentos
            from .context_builder import ContextBuilder
            context_builder = ContextBuilder()
            context_text = await context_builder.combine_simple_documents(retrieved_documents)
            
            # Obtener estadísticas del contexto
            context_stats = await context_builder.get_simple_context_statistics(context_text, retrieved_documents)
            
            if conversation_history and len(conversation_history) >= 2:
                # Prompt de seguimiento si hay historial
                last_qa = conversation_history[-1]
                original_question = last_qa.get("question", "")
                original_answer = last_qa.get("answer", "")
                
                prompt_result = await self.prompt_builder.build_followup_prompt(
                    original_question=original_question,
                    original_answer=original_answer,
                    followup_question=question,
                    context=context_text
                )
            else:
                # Prompt de Q&A estándar
                prompt_result = await self.prompt_builder.build_qa_prompt(
                    question=question,
                    context=context_text,
                    context_stats=context_stats
                )
            
            system_prompt = prompt_result["system"]
            user_prompt = prompt_result["user"]
            
            # Crear metadatos del prompt
            prompt_metadata = await self.prompt_builder.get_prompt_preview(
                question=question,
                context=context_text
            )
            
            print(f"   ✅ Prompt construido:")
            print(f"      📋 Sistema: {len(system_prompt)} caracteres")
            print(f"      👤 Usuario: {len(user_prompt)} caracteres")
            print(f"      📊 Contexto estimado: {prompt_metadata.get('estimated_total_length', 'N/A')} caracteres")
            
            # Actualizar estadística de longitud de contexto
            context_length = int(prompt_metadata.get('estimated_total_length', '0'))
            if self.rag_stats["total_rag_requests"] > 1:
                current_avg = self.rag_stats["average_context_length"]
                new_avg = ((current_avg * (self.rag_stats["total_rag_requests"] - 1)) + context_length) / self.rag_stats["total_rag_requests"]
                self.rag_stats["average_context_length"] = int(new_avg)
            else:
                self.rag_stats["average_context_length"] = context_length
            
            # Paso 1.2b: Enviar a OpenAI
            print("🤖 Enviando a OpenAI...")
            
            generation_result = await self.openai_service.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                custom_max_tokens=custom_max_tokens,
                custom_temperature=custom_temperature
            )
            
            # Verificar si la generación fue exitosa
            if not generation_result.get("success", False):
                self.rag_stats["failed_generations"] += 1
                print(f"❌ Error en generación: {generation_result.get('error', 'Error desconocido')}")
                return self._build_error_response(
                    question=question,
                    retrieved_documents=retrieved_documents,
                    error=generation_result.get("error", "Error en generación"),
                    start_time=start_time
                )
            
            # Paso 1.2c: Procesar respuesta exitosa
            self.rag_stats["successful_generations"] += 1
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # Actualizar estadística de tiempo de respuesta
            if self.rag_stats["successful_generations"] > 1:
                current_avg = self.rag_stats["average_response_time"]
                new_avg = ((current_avg * (self.rag_stats["successful_generations"] - 1)) + total_time) / self.rag_stats["successful_generations"]
                self.rag_stats["average_response_time"] = int(round(new_avg * 1000))  # Convertir a milisegundos enteros
            else:
                self.rag_stats["average_response_time"] = int(round(total_time * 1000))  # Convertir a milisegundos enteros
            
            # Extraer IDs de documentos fuente
            source_document_ids = [doc.id for doc in retrieved_documents if hasattr(doc, 'id') and doc.id]
            
            # Construir respuesta completa
            rag_response = {
                "answer": generation_result["answer"],
                "source_document_ids": source_document_ids,
                "question": question,
                "timestamp": end_time.isoformat(),
                "total_response_time_seconds": total_time,
                "success": True
            }
            
            # Agregar metadatos si se solicita
            if include_metadata:
                rag_response["metadata"] = {
                    "generation": {
                        "model_used": generation_result.get("model_used"),
                        "response_time_seconds": generation_result.get("response_time_seconds"),
                        "usage": generation_result.get("usage", {}),
                        "configuration": generation_result.get("configuration", {})
                    },
                    "prompt": prompt_metadata,
                    "retrieval": {
                        "documents_count": len(retrieved_documents),
                        "source_document_ids": source_document_ids,
                        "has_conversation_history": bool(conversation_history)
                    },
                    "rag_service": {
                        "total_requests": self.rag_stats["total_rag_requests"],
                        "success_rate": (self.rag_stats["successful_generations"] / self.rag_stats["total_rag_requests"]) * 100,
                        "average_response_time": self.rag_stats["average_response_time"]
                    }
                }
            
            print(f"✅ Respuesta RAG generada exitosamente:")
            print(f"   📝 Respuesta: {len(rag_response['answer'])} caracteres")
            print(f"   📚 Documentos fuente: {len(source_document_ids)}")
            print(f"   ⏱️ Tiempo total: {total_time:.2f}s")
            
            return rag_response
            
        except Exception as e:
            # Manejar errores inesperados
            self.rag_stats["failed_generations"] += 1
            print(f"❌ Error inesperado en generación RAG: {str(e)}")
            
            return self._build_error_response(
                question=question,
                retrieved_documents=retrieved_documents,
                error=f"Error inesperado: {str(e)}",
                start_time=start_time
            )
    
    def _build_error_response(
        self,
        question: str,
        retrieved_documents: List[Document],
        error: str,
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        Construye una respuesta de error estandarizada
        
        Args:
            question: Pregunta original
            retrieved_documents: Documentos que se intentaron usar
            error: Mensaje de error
            start_time: Tiempo de inicio para calcular duración
            
        Returns:
            Diccionario con información del error
        """
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        return {
            "answer": None,
            "source_document_ids": [doc.id for doc in retrieved_documents if hasattr(doc, 'id') and doc.id],
            "question": question,
            "error": error,
            "timestamp": end_time.isoformat(),
            "total_response_time_seconds": total_time,
            "success": False
        }
    
    async def generate_simple_answer(
        self,
        question: str,
        context_text: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera una respuesta simple con contexto de texto plano
        
        Args:
            question: Pregunta del usuario
            context_text: Contexto como texto plano
            custom_instructions: Instrucciones personalizadas
            
        Returns:
            Diccionario con respuesta
        """
        print(f"🔄 Generación simple con contexto de texto...")
        
        # Crear prompt simple
        system_prompt = self.prompt_builder.system_instructions
        if custom_instructions:
            system_prompt += f"\n\nInstrucciones adicionales: {custom_instructions}"
        
        user_prompt = f"Contexto:\n{context_text}\n\nPregunta: {question}"
        
        # Generar respuesta
        result = await self.openai_service.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        return {
            "answer": result.get("answer"),
            "question": question,
            "success": result.get("success", False),
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "generation": result,
                "context_length": len(context_text)
            }
        }
    
    def get_rag_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio RAG
        
        Returns:
            Diccionario con estadísticas detalladas
        """
        stats = self.rag_stats.copy()
        
        # Calcular métricas adicionales
        if stats["total_rag_requests"] > 0:
            stats["success_rate_percentage"] = int(round((stats["successful_generations"] / stats["total_rag_requests"]) * 100))
            stats["average_documents_per_request"] = int(round(stats["total_documents_processed"] / stats["total_rag_requests"]))
        else:
            stats["success_rate_percentage"] = 0
            stats["average_documents_per_request"] = 0
        
        # Agregar estadísticas del servicio OpenAI
        openai_stats = self.openai_service.get_usage_statistics()
        stats["openai_service"] = openai_stats
        
        return stats
    
    def reset_statistics(self):
        """
        Reinicia todas las estadísticas
        """
        self.rag_stats: Dict[str, Any] = {
            "total_rag_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_documents_processed": 0,
            "average_context_length": 0,
            "average_response_time": 0
        }
        
        self.openai_service.reset_statistics()
        print("📊 Estadísticas RAG reiniciadas")
    
    def update_configuration(
        self,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_instructions: Optional[str] = None
    ):
        """
        Actualiza la configuración del servicio RAG
        
        Args:
            model: Nuevo modelo
            max_tokens: Nuevo límite de tokens
            temperature: Nueva temperatura
            system_instructions: Nuevas instrucciones del sistema
        """
        # Actualizar servicio OpenAI
        self.openai_service.update_configuration(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Actualizar prompt builder
        if system_instructions is not None:
            self.prompt_builder.update_configuration(system_instructions=system_instructions)
            print(f"🔄 Instrucciones del sistema actualizadas")
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual del servicio RAG
        
        Returns:
            Diccionario con configuración completa
        """
        return {
            "openai_service": self.openai_service.get_configuration(),
            "prompt_builder": self.prompt_builder.get_configuration(),
            "rag_statistics": self.get_rag_statistics()
        }