from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict
from datetime import datetime
import uuid

class ResponseMetadata(BaseModel):
    """Metadatos de la respuesta"""
    
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="ID único de la petición"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de la petición"
    )
    route: str = Field(
        description="Ruta completa del endpoint",
    )

class StandardResponse(BaseModel):
    """Esquema estándar de respuesta para todos los endpoints"""
    
    status: str = Field(
        description="Estado de la operación",
    )
    code: int = Field(
        description="Código de estado HTTP",
    )
    data: Optional[Any] = Field(
        None,
        description="Datos de la respuesta"
    )
    message: str = Field(
        description="Mensaje sobre la operación",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Lista de errores si los hay"
    )
    metadata: ResponseMetadata = Field(
        description="Metadatos de la respuesta"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SuccessResponse(StandardResponse):
    """Respuesta exitosa estándar"""
    
    status: str = Field(default="success")
    code: int = Field(default=200)
    message: str = Field(default="Operación completada exitosamente")

class ErrorResponse(StandardResponse):
    """Respuesta de error estándar"""
    
    status: str = Field(default="error")
    data: Optional[Any] = Field(default=None)
    
    @classmethod
    def create_error_response(
        cls,
        code: int,
        message: str,
        errors: Optional[List[str]] = None,
        route: str = "",
        data: Any = None
    ) -> "ErrorResponse":
        """Crea una respuesta de error estándar"""
        return cls(
            code=code,
            message=message,
            errors=errors or [],
            data=data,
            metadata=ResponseMetadata(route=route)
        )

def create_success_response(
    data: Any = None,
    message: str = "Operación completada exitosamente",
    code: int = 200,
    route: str = ""
) -> StandardResponse:
    """Función helper para crear respuestas exitosas"""
    return SuccessResponse(
        code=code,
        data=data,
        message=message,
        metadata=ResponseMetadata(route=route)
    )

def create_error_response(
    code: int,
    message: str,
    errors: Optional[List[str]] = None,
    route: str = "",
    data: Any = None
) -> StandardResponse:
    """Función helper para crear respuestas de error"""
    return ErrorResponse.create_error_response(
        code=code,
        message=message,
        errors=errors,
        route=route,
        data=data
    )