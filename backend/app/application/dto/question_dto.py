from pydantic import BaseModel, Field, validator
from typing import Optional

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
    """DTO para respuestas de preguntas"""
    
    answer: str = Field(
        description="La respuesta generada",
    )
    question: str = Field(
        description="La pregunta original",
    )
    status: str = Field(
        description="Estado de la respuesta",
    )
    confidence: Optional[float] = Field(
        description="Nivel de confianza de la respuesta (0-1)",
    )
    processing_time_ms: Optional[int] = Field(
        description="Tiempo de procesamiento en milisegundos",
    )