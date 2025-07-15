from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI
import os
from datetime import datetime
import json
import logging

class OpenAIGenerationService:
    """Servicio para generación de respuestas usando GPT-4o-mini (Paso 3 - Generación)"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        temperature: float = 0.1,
        timeout: int = 30
    ):
        self.logger = logging.getLogger(__name__)
        """
        Inicializa el servicio de generación con OpenAI
        
        Args:
            api_key: Clave API de OpenAI (si no se proporciona, usa variable de entorno)
            model: Modelo a usar (por defecto gpt-4o-mini)
            max_tokens: Máximo número de tokens en la respuesta
            temperature: Temperatura para controlar creatividad (0.0-1.0)
            timeout: Timeout en segundos para las requests
        """
        # Configurar API key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key de OpenAI no encontrada. Proporciona api_key o configura OPENAI_API_KEY")
        
        # Configurar cliente OpenAI
        self.client = OpenAI(api_key=self.api_key)
        
        # Configuración del modelo
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        # Estadísticas de uso
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens_used": 0,
            "total_cost_estimate": 0.0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        
        self.logger.info(f"🤖 OpenAIGenerationService inicializado:")
        self.logger.info(f"   🎯 Modelo: {model}")
        self.logger.info(f"   📊 Max tokens: {max_tokens}")
        self.logger.info(f"   🌡️ Temperature: {temperature}")
        self.logger.info(f"   ⏱️ Timeout: {timeout}s")
        
        # Verificar conexión con OpenAI
        self._verify_connection()
    
    def _verify_connection(self):
        """
        Verifica la conexión con OpenAI y la validez del modelo
        """
        try:
            self.logger.info("🔍 Verificando conexión con OpenAI...")
            
            # Hacer una request de prueba simple
            test_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente de prueba."},
                    {"role": "user", "content": "Di 'conexión exitosa'"}
                ],
                max_tokens=10,
                temperature=0.0
            )
            
            if test_response.choices and test_response.choices[0].message.content:
                self.logger.info("✅ Conexión con OpenAI verificada exitosamente")
                self.logger.info(f"   📝 Respuesta de prueba: {test_response.choices[0].message.content.strip()}")
                
                # Actualizar estadísticas
                if test_response.usage:
                    self.logger.info(f"   📊 Tokens usados en prueba: {test_response.usage.total_tokens}")
            else:
                self.logger.warning("⚠️ Conexión establecida pero respuesta vacía")
                
        except Exception as e:
            self.logger.error(f"❌ Error al verificar conexión con OpenAI: {str(e)}")
            raise ConnectionError(f"No se pudo conectar con OpenAI: {str(e)}")
    
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        custom_max_tokens: Optional[int] = None,
        custom_temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Genera una respuesta usando GPT-4o-mini (Paso 1.1 completado)
        
        Args:
            system_prompt: Prompt del sistema con instrucciones
            user_prompt: Prompt del usuario con contexto y pregunta
            custom_max_tokens: Límite personalizado de tokens (opcional)
            custom_temperature: Temperatura personalizada (opcional)
            
        Returns:
            Diccionario con respuesta y metadatos
        """
        self.logger.info(f"🚀 Generando respuesta con {self.model}...")
        self.logger.info(f"   📋 Sistema: {len(system_prompt)} caracteres")
        self.logger.info(f"   👤 Usuario: {len(user_prompt)} caracteres")
        
        # Usar configuración personalizada o por defecto
        max_tokens = custom_max_tokens or self.max_tokens
        temperature = custom_temperature if custom_temperature is not None else self.temperature
        
        try:
            # Registrar inicio de request
            start_time = datetime.now()
            self.usage_stats["total_requests"] += 1
            
            # Hacer request a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )
            
            # Calcular tiempo de respuesta
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Extraer respuesta
            if not response.choices or not response.choices[0].message.content:
                raise ValueError("Respuesta vacía de OpenAI")
            
            answer = response.choices[0].message.content.strip()
            
            # Procesar información de uso
            usage_info = {}
            if response.usage:
                usage_info = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                # Actualizar estadísticas globales
                self.usage_stats["total_tokens_used"] += response.usage.total_tokens
                self.usage_stats["successful_requests"] += 1
                
                # Estimar costo (precios aproximados para gpt-4o-mini)
                input_cost = (response.usage.prompt_tokens / 1000) * 0.00015  # $0.15 per 1K input tokens
                output_cost = (response.usage.completion_tokens / 1000) * 0.0006  # $0.60 per 1K output tokens
                total_cost = input_cost + output_cost
                self.usage_stats["total_cost_estimate"] += total_cost
            else:
                total_cost = 0.0
            
            # Preparar respuesta completa
            generation_result = {
                "answer": answer,
                "model_used": self.model,
                "timestamp": end_time.isoformat(),
                "response_time_seconds": response_time,
                "usage": usage_info,
                "configuration": {
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "model": self.model
                },
                "success": True
            }
            
            self.logger.info(f"✅ Respuesta generada exitosamente:")
            self.logger.info(f"   📝 Longitud: {len(answer)} caracteres")
            self.logger.info(f"   ⏱️ Tiempo: {response_time:.2f}s")
            if usage_info:
                self.logger.info(f"   📊 Tokens: {usage_info.get('total_tokens', 'N/A')}")
                self.logger.info(f"   💰 Costo estimado: ${total_cost:.6f}")
            
            return generation_result
            
        except Exception as e:
            # Registrar error
            self.usage_stats["failed_requests"] += 1
            error_time = datetime.now()
            
            error_result = {
                "answer": None,
                "error": str(e),
                "model_used": self.model,
                "timestamp": error_time.isoformat(),
                "success": False,
                "configuration": {
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "model": self.model
                }
            }
            
            self.logger.error(f"❌ Error al generar respuesta: {str(e)}")
            return error_result
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso del servicio
        
        Returns:
            Diccionario con estadísticas detalladas
        """
        stats = self.usage_stats.copy()
        
        # Calcular métricas adicionales
        if stats["total_requests"] > 0:
            stats["success_rate"] = (stats["successful_requests"] / stats["total_requests"]) * 100
            stats["average_tokens_per_request"] = stats["total_tokens_used"] / stats["successful_requests"] if stats["successful_requests"] > 0 else 0
        else:
            stats["success_rate"] = 0
            stats["average_tokens_per_request"] = 0
        
        return stats
    
    def reset_statistics(self):
        """
        Reinicia las estadísticas de uso
        """
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens_used": 0,
            "total_cost_estimate": 0.0,
            "successful_requests": 0,
            "failed_requests": 0
        }
        self.logger.info("📊 Estadísticas de uso reiniciadas")
    
    def update_configuration(
        self,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None
    ):
        """
        Actualiza la configuración del servicio
        
        Args:
            model: Nuevo modelo a usar
            max_tokens: Nuevo límite de tokens
            temperature: Nueva temperatura
            timeout: Nuevo timeout
        """
        if model is not None:
            old_model = self.model
            self.model = model
            self.logger.info(f"🔄 Modelo actualizado: '{old_model}' → '{model}'")
        
        if max_tokens is not None:
            old_tokens = self.max_tokens
            self.max_tokens = max_tokens
            self.logger.info(f"🔄 Max tokens actualizado: {old_tokens} → {max_tokens}")
        
        if temperature is not None:
            old_temp = self.temperature
            self.temperature = temperature
            self.logger.info(f"🔄 Temperature actualizada: {old_temp} → {temperature}")
        
        if timeout is not None:
            old_timeout = self.timeout
            self.timeout = timeout
            self.logger.info(f"🔄 Timeout actualizado: {old_timeout}s → {timeout}s")
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual del servicio
        
        Returns:
            Diccionario con la configuración
        """
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "api_key_configured": bool(self.api_key),
            "supported_models": ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
        }
    
    async def test_model_availability(self, model_name: str) -> bool:
        """
        Prueba si un modelo específico está disponible
        
        Args:
            model_name: Nombre del modelo a probar
            
        Returns:
            True si el modelo está disponible, False en caso contrario
        """
        try:
            self.logger.info(f"🧪 Probando disponibilidad del modelo: {model_name}")
            
            test_response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Test"},
                    {"role": "user", "content": "Hi"}
                ],
                max_tokens=5,
                temperature=0.0
            )
            
            if test_response.choices:
                self.logger.info(f"✅ Modelo {model_name} disponible")
                return True
            else:
                self.logger.warning(f"❌ Modelo {model_name} no disponible")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error al probar modelo {model_name}: {str(e)}")
            return False