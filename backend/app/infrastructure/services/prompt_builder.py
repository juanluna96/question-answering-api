from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

class PromptBuilder:
    """Servicio para preparar prompts para OpenAI (Paso 3 de Aumento)"""
    
    def __init__(
        self,
        response_format: str = "detailed",
        include_metadata: bool = True,
        system_instructions: Optional[str] = None
    ):
        self.logger = logging.getLogger(__name__)
        self.system_instructions = system_instructions or self._get_default_system_instructions()
        self.response_format = response_format
        self.include_metadata = include_metadata
        
        self.logger.info(f"🔧 PromptBuilder inicializado:")
        self.logger.info(f"   📝 Formato de respuesta: {response_format}")
        self.logger.info(f"   📊 Incluir metadatos: {include_metadata}")
        self.logger.info(f"   📋 Instrucciones del sistema: {len(self.system_instructions)} caracteres")
    
    async def build_qa_prompt(
        self,
        question: str,
        context: str,
        context_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Construye un prompt completo para Q&A con contexto
        
        Args:
            question: Pregunta del usuario
            context: Contexto recuperado y limitado
            context_stats: Estadísticas del contexto (opcional)
            
        Returns:
            Diccionario con 'system' y 'user' prompts
        """
        self.logger.info(f"🔨 Construyendo prompt Q&A...")
        self.logger.info(f"   ❓ Pregunta: {len(question)} caracteres")
        self.logger.info(f"   📄 Contexto: {len(context)} caracteres")
        
        # Construir prompt del sistema
        system_prompt = self._build_system_prompt(context_stats)
        
        # Construir prompt del usuario
        user_prompt = self._build_user_prompt(question, context, context_stats)
        
        prompt_data = {
            "system": system_prompt,
            "user": user_prompt
        }
        
        self.logger.info(f"✅ Prompt construido exitosamente:")
        self.logger.info(f"   📋 Sistema: {len(system_prompt)} caracteres")
        self.logger.info(f"   👤 Usuario: {len(user_prompt)} caracteres")
        self.logger.info(f"   📊 Total: {len(system_prompt) + len(user_prompt)} caracteres")
        
        return prompt_data
    
    def _build_system_prompt(self, context_stats: Optional[Dict[str, Any]] = None) -> str:
        """
        Construye el prompt del sistema con instrucciones específicas
        """
        system_parts = []
        
        # Instrucciones base del sistema
        system_parts.append(self.system_instructions)
        
        # Agregar instrucciones específicas según el formato
        format_instructions = self._get_format_instructions()
        if format_instructions:
            system_parts.append(format_instructions)
        
        # Agregar información del contexto si está disponible
        if self.include_metadata and context_stats:
            context_info = self._build_context_metadata(context_stats)
            if context_info:
                system_parts.append(context_info)
        
        # Agregar instrucciones de calidad
        quality_instructions = self._get_quality_instructions()
        system_parts.append(quality_instructions)
        
        return "\n\n".join(system_parts)
    
    def _build_user_prompt(
        self,
        question: str,
        context: str,
        context_stats: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construye el prompt del usuario con contexto y pregunta
        """
        user_parts = []
        
        # Encabezado del contexto
        context_header = self._build_context_header(context_stats)
        user_parts.append(context_header)
        
        # Contexto de documentos
        user_parts.append("CONTEXTO:")
        user_parts.append(context)
        
        # Separador
        user_parts.append("=" * 50)
        
        # Pregunta del usuario
        user_parts.append("PREGUNTA:")
        user_parts.append(question)
        
        # Instrucciones finales
        final_instructions = self._get_final_instructions()
        user_parts.append(final_instructions)
        
        return "\n\n".join(user_parts)
    
    def _get_default_system_instructions(self) -> str:
        """
        Obtiene las instrucciones por defecto del sistema
        """
        return """Eres un asistente de IA especializado en responder preguntas basándote en documentos proporcionados.

Tus responsabilidades:
1. Analizar cuidadosamente el contexto proporcionado
2. Responder únicamente basándote en la información disponible en los documentos
3. Ser preciso, claro y conciso en tus respuestas
4. Indicar claramente cuando la información no está disponible en el contexto
5. Citar los documentos relevantes cuando sea apropiado

Principios importantes:
- NO inventes información que no esté en los documentos
- Si la respuesta no está en el contexto, dilo claramente
- Mantén un tono profesional y útil
- Estructura tu respuesta de manera clara y organizada"""
    
    def _get_format_instructions(self) -> str:
        """
        Obtiene instrucciones específicas según el formato de respuesta
        """
        format_map = {
            "detailed": """FORMATO DE RESPUESTA DETALLADO:
- Proporciona una respuesta completa y bien estructurada
- Incluye detalles relevantes y contexto adicional
- Organiza la información en párrafos claros
- Menciona las fuentes de información cuando sea relevante""",
            
            "concise": """FORMATO DE RESPUESTA CONCISO:
- Proporciona una respuesta directa y al punto
- Limita la respuesta a la información esencial
- Evita detalles innecesarios
- Máximo 2-3 párrafos""",
            
            "structured": """FORMATO DE RESPUESTA ESTRUCTURADO:
- Organiza la respuesta en secciones claras
- Usa viñetas o numeración cuando sea apropiado
- Incluye un resumen al final si es relevante
- Separa hechos de interpretaciones"""
        }
        
        return format_map.get(self.response_format, "")
    
    def _build_context_metadata(self, context_stats: Dict[str, Any]) -> str:
        """
        Construye información de metadatos del contexto
        """
        if not context_stats:
            return ""
        
        metadata_parts = ["INFORMACIÓN DEL CONTEXTO:"]
        
        # Información básica
        if "total_documents" in context_stats:
            metadata_parts.append(f"- Documentos analizados: {context_stats['total_documents']}")
        
        if "estimated_tokens" in context_stats:
            metadata_parts.append(f"- Tokens estimados: {context_stats['estimated_tokens']:,}")
        
        # Información de limitación si está disponible
        if context_stats.get("limited", False):
            metadata_parts.append("- Contexto limitado por restricciones de longitud")
            if "documents_removed" in context_stats:
                metadata_parts.append(f"- Documentos excluidos: {context_stats['documents_removed']}")
        
        # Información de scores si está disponible
        if "documents" in context_stats and "avg_score" in context_stats["documents"]:
            avg_score = context_stats["documents"]["avg_score"]
            metadata_parts.append(f"- Relevancia promedio: {avg_score:.3f}")
        
        return "\n".join(metadata_parts)
    
    def _build_context_header(self, context_stats: Optional[Dict[str, Any]] = None) -> str:
        """
        Construye el encabezado del contexto
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_parts = [
            f"Consulta procesada: {timestamp}",
            "Los siguientes documentos contienen información relevante para tu pregunta:"
        ]
        
        if context_stats and self.include_metadata:
            if "total_documents" in context_stats:
                header_parts.append(f"Total de documentos: {context_stats['total_documents']}")
        
        return "\n".join(header_parts)
    
    def _get_quality_instructions(self) -> str:
        """
        Obtiene instrucciones de calidad para la respuesta
        """
        return """CRITERIOS DE CALIDAD:
- Verifica que tu respuesta esté completamente basada en el contexto proporcionado
- Si necesitas hacer inferencias, hazlo claro y justifica tu razonamiento
- Si la información es insuficiente, sugiere qué información adicional sería útil
- Mantén un equilibrio entre completitud y claridad"""
    
    def _get_final_instructions(self) -> str:
        """
        Obtiene las instrucciones finales para el usuario
        """
        return """Por favor, responde la pregunta basándote únicamente en el contexto proporcionado arriba. Si la información no está disponible en los documentos, indícalo claramente."""
    
    async def build_followup_prompt(
        self,
        original_question: str,
        original_answer: str,
        followup_question: str,
        context: str
    ) -> Dict[str, str]:
        """
        Construye un prompt para preguntas de seguimiento
        
        Args:
            original_question: Pregunta original
            original_answer: Respuesta original
            followup_question: Pregunta de seguimiento
            context: Contexto actualizado
            
        Returns:
            Diccionario con prompts del sistema y usuario
        """
        self.logger.info(f"🔄 Construyendo prompt de seguimiento...")
        
        # Sistema con contexto de conversación
        system_prompt = f"""{self.system_instructions}

CONTEXTO DE CONVERSACIÓN:
Esta es una pregunta de seguimiento en una conversación existente. Mantén coherencia con la respuesta anterior mientras proporcionas nueva información basada en el contexto actualizado."""
        
        # Usuario con historial
        user_prompt = f"""HISTORIAL DE CONVERSACIÓN:

Pregunta anterior: {original_question}
Respuesta anterior: {original_answer}

{"=" * 50}

CONTEXTO ACTUALIZADO:
{context}

{"=" * 50}

NUEVA PREGUNTA:
{followup_question}

Por favor, responde la nueva pregunta considerando el contexto de la conversación anterior y basándote en el contexto actualizado proporcionado."""
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    async def validate_prompt(
        self,
        prompt_data: Dict[str, str],
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Valida que el prompt esté dentro de los límites
        
        Args:
            prompt_data: Datos del prompt a validar
            max_tokens: Límite máximo de tokens
            
        Returns:
            Información de validación
        """
        total_chars = sum(len(content) for content in prompt_data.values())
        estimated_tokens = total_chars // 4  # Estimación aproximada
        
        validation_result = {
            "valid": estimated_tokens <= max_tokens,
            "total_characters": total_chars,
            "estimated_tokens": estimated_tokens,
            "max_tokens": max_tokens,
            "token_usage_percentage": (estimated_tokens / max_tokens) * 100,
            "tokens_remaining": max(0, max_tokens - estimated_tokens)
        }
        
        # Agregar detalles por sección
        validation_result["sections"] = {
            section: {
                "characters": len(content),
                "estimated_tokens": len(content) // 4
            }
            for section, content in prompt_data.items()
        }
        
        if validation_result["valid"]:
            self.logger.info(f"✅ Prompt válido: {estimated_tokens:,}/{max_tokens:,} tokens")
        else:
            self.logger.warning(f"⚠️ Prompt excede límites: {estimated_tokens:,}/{max_tokens:,} tokens")
        
        return validation_result
    
    def update_configuration(
        self,
        system_instructions: Optional[str] = None,
        response_format: Optional[str] = None,
        include_metadata: Optional[bool] = None
    ):
        """
        Actualiza la configuración del constructor de prompts
        
        Args:
            system_instructions: Nuevas instrucciones del sistema
            response_format: Nuevo formato de respuesta
            include_metadata: Si incluir metadatos
        """
        if system_instructions is not None:
            old_length = len(self.system_instructions)
            self.system_instructions = system_instructions
            self.logger.info(f"🔄 Instrucciones actualizadas: {old_length} → {len(system_instructions)} chars")
        
        if response_format is not None:
            old_format = self.response_format
            self.response_format = response_format
            self.logger.info(f"🔄 Formato actualizado: '{old_format}' → '{response_format}'")
        
        if include_metadata is not None:
            old_metadata = self.include_metadata
            self.include_metadata = include_metadata
            self.logger.info(f"🔄 Metadatos actualizado: {old_metadata} → {include_metadata}")
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual del constructor
        
        Returns:
            Diccionario con la configuración
        """
        return {
            "response_format": self.response_format,
            "include_metadata": self.include_metadata,
            "system_instructions_length": len(self.system_instructions),
            "available_formats": ["detailed", "concise", "structured"]
        }
    
    async def get_prompt_preview(
        self,
        question: str,
        context: str,
        max_preview_length: int = 500
    ) -> Dict[str, str]:
        """
        Obtiene una vista previa del prompt sin construirlo completamente
        
        Args:
            question: Pregunta del usuario
            context: Contexto disponible
            max_preview_length: Longitud máxima de la vista previa
            
        Returns:
            Vista previa del prompt
        """
        system_preview = self.system_instructions[:max_preview_length]
        if len(self.system_instructions) > max_preview_length:
            system_preview += "..."
        
        context_preview = context[:max_preview_length]
        if len(context) > max_preview_length:
            context_preview += "..."
        
        return {
            "system_preview": system_preview,
            "context_preview": context_preview,
            "question": question,
            "estimated_total_length": str(len(self.system_instructions) + len(context) + len(question) + 200)  # +200 para estructura
        }