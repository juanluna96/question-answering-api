from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List

class QuestionRequestDTO(BaseModel):
    """DTO para solicitudes de preguntas"""
    
    question: str = Field(
        description="La pregunta a responder",
    )
    
    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError('La pregunta no puede estar vacía')
        
        # Eliminar espacios extra
        v = v.strip()
        
        # Verificar que no sea solo espacios o caracteres especiales
        if not any(c.isalnum() for c in v):
            raise ValueError('La pregunta debe contener al menos un carácter alfanumérico')
        
        # Verificar longitud mínima después de limpiar
        if len(v) < 3:
            raise ValueError('La pregunta debe tener al menos 3 caracteres')
            
        return v

class AnswerResponseDTO(BaseModel):
    """DTO para respuestas de preguntas con soporte para metadatos RAG"""
    
    answer: str = Field(
        description="La respuesta generada",
    )
    question: str = Field(
        description="La pregunta original",
    )
    status: str = Field(
        description="Estado de la respuesta (success, error, validation_error)",
    )
    confidence: Optional[float] = Field(
        description="Nivel de confianza de la respuesta (0-1)",
        ge=0.0,
        le=1.0
    )
    processing_time_ms: Optional[int] = Field(
        description="Tiempo de procesamiento en milisegundos",
        ge=0
    )
    sources: Optional[List[str]] = Field(
        description="IDs de los documentos usados como fuente",
        default=None
    )
    metadata: Optional[Dict[str, Any]] = Field(
        description="Metadatos adicionales del proceso RAG (opcional)",
        default=None
    )
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = {'success', 'error', 'validation_error'}
        if v not in allowed_statuses:
            raise ValueError(f'Status debe ser uno de: {", ".join(allowed_statuses)}')
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence debe estar entre 0.0 y 1.0')
        return v