from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional, List
import json
import time
from .response_models import create_success_response, create_error_response

class StandardResponseMiddleware(BaseHTTPMiddleware):
    """Middleware para estandarizar todas las respuestas de la API"""
    
    def __init__(self, app, exclude_routes: Optional[List[str]] = None):
        super().__init__(app)
        # Rutas que no deben ser transformadas (docs, redoc, openapi.json)
        self.exclude_routes = exclude_routes or [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa la petición y estandariza la respuesta"""
        start_time = time.time()
        
        # Verificar si la ruta debe ser excluida
        if any(request.url.path.startswith(route) for route in self.exclude_routes):
            return await call_next(request)
        
        try:
            # Ejecutar la petición
            response = await call_next(request)
            
            # Solo procesar respuestas JSON
            if not self._is_json_response(response):
                return response
            
            # Obtener el contenido de la respuesta
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Parsear el contenido JSON
            try:
                original_data = json.loads(response_body.decode())
            except json.JSONDecodeError:
                # Si no es JSON válido, retornar la respuesta original
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            
            # Verificar si ya tiene el formato estándar
            if self._is_standard_format(original_data):
                return JSONResponse(
                    content=original_data,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            
            # Crear respuesta estándar
            if 200 <= response.status_code < 300:
                standard_response = create_success_response(
                    data=original_data,
                    code=response.status_code,
                    route=str(request.url.path)
                )
            else:
                # Para errores, extraer mensaje si existe
                error_message = "Error en la operación"
                errors = []
                
                if isinstance(original_data, dict):
                    error_message = original_data.get("detail", error_message)
                    if "detail" in original_data and isinstance(original_data["detail"], list):
                        errors = [{"field": "general", "type": "Detail Error", "message": str(err)} for err in original_data["detail"]]
                    elif "detail" in original_data:
                        errors = [{"field": "general", "type": "Detail Error", "message": str(original_data["detail"])}]
                
                standard_response = create_error_response(
                    code=response.status_code,
                    message=error_message,
                    errors=errors,
                    route=str(request.url.path),
                    data=original_data if response.status_code != 422 else None
                )
            
            # Retornar respuesta estandarizada
            return JSONResponse(
                content=standard_response.dict(),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            # Manejar errores del middleware
            error_response = create_error_response(
                code=500,
                message="Error interno del servidor",
                errors=[{"field": "general", "type": "Middleware Error", "message": str(e)}],
                route=str(request.url.path)
            )
            
            return JSONResponse(
                content=error_response.dict(),
                status_code=500
            )
    
    def _is_json_response(self, response: Response) -> bool:
        """Verifica si la respuesta es JSON"""
        content_type = response.headers.get("content-type", "")
        return "application/json" in content_type
    
    def _is_standard_format(self, data: dict) -> bool:
        """Verifica si los datos ya tienen el formato estándar"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ["status", "code", "message", "metadata"]
        return all(field in data for field in required_fields)