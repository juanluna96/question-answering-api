from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
from .infrastructure.config.dependency_container import DependencyContainer
from .infrastructure.web.question_controller import QuestionController
from .infrastructure.web.response_middleware import StandardResponseMiddleware
from .infrastructure.web.response_models import create_success_response, create_error_response

# Instancia global del contenedor de dependencias
dependency_container = DependencyContainer()

# Configuración de la aplicación
app_config = {
    "title": "Question Answering API",
    "description": "API para procesamiento de preguntas y respuestas",
    "version": "1.0.0"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Iniciando Question Answering API...")
    
    # Verificar configuración crítica
    config = dependency_container.get_config()
    if not config.get("openai_api_key"):
        print("⚠️  ADVERTENCIA: OPENAI_API_KEY no está configurada")
    
    print(f"📊 Modelo configurado: {config.get('openai_model')}")
    print(f"💾 Caché por defecto: {config.get('default_cache_path')}")
    
    yield
    
    # Shutdown
    print("🛑 Cerrando Question Answering API...")
    dependency_container.clear_instances()

# Crear aplicación FastAPI
app = FastAPI(
    title=app_config["title"],
    description=app_config["description"],
    version=app_config["version"],
    lifespan=lifespan
)

# Inicializar controlador
question_controller = QuestionController()

# Configurar middlewares
# Middleware de respuesta estándar (debe ir antes que CORS)
app.add_middleware(StandardResponseMiddleware)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir router del controlador
app.include_router(question_controller.get_router())

# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz que muestra información de la API"""
    api_info = {
        "name": "Question Answering API",
        "version": app_config["version"],
        "description": app_config["description"],
        "endpoints": {
            "/": "Información de la API",
            "/health": "Estado de salud de la API",
            "/docs": "Documentación interactiva (Swagger UI)",
            "/redoc": "Documentación alternativa (ReDoc)",
            "/answer": "Procesar pregunta (POST)"
        }
    }
    
    return create_success_response(
        data=api_info,
        message="Información de la API obtenida exitosamente",
        route="/"
    )

# Health check
@app.get("/health")
async def health_check():
    """Health check global de la aplicación"""
    try:
        config = dependency_container.get_config()
        
        health_data = {
            "status": "healthy",
            "service": "question-answering-api",
            "version": app_config["version"],
            "config": {
                "openai_configured": bool(config.get("openai_api_key")),
                "model": config.get("openai_model"),
                "cache_path": config.get("default_cache_path")
            }
        }
        
        return create_success_response(
            data=health_data,
            message="Servicio funcionando correctamente",
            route="/health"
        )
        
    except Exception as e:
        from .infrastructure.web.response_models import create_error_response
        return create_error_response(
            code=500,
            message="Error en health check",
            errors=[{"field": "general", "type": "Internal Error", "message": str(e)}],
            route="/health"
        )

# Manejo de errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejo de errores de validación de Pydantic"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Omitir 'body'
        errors.append({
            "field": field,
            "type": error["type"].replace("_", " ").title(),
            "message": error["msg"].replace(f"Value error, ", "")
        })
    
    error_response = create_error_response(
        code=422,
        message="Error de validación en los datos enviados",
        errors=errors,
        route=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode='json')
    )

# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo global de excepciones"""
    print(f"Error global: {exc}")
    
    error_response = create_error_response(
        code=500,
        message="Error interno del servidor",
        errors=[{"field": "general", "type": "Internal Error", "message": str(exc)}],
        route=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode='json')
    )

if __name__ == "__main__":
    import uvicorn
    
    # Configuración para desarrollo
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )