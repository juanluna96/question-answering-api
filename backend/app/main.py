from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from .infrastructure.config.dependency_container import DependencyContainer
from .infrastructure.web.question_controller import QuestionController
from .infrastructure.web.response_middleware import StandardResponseMiddleware
from .infrastructure.web.response_models import create_success_response

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
            errors=[str(e)],
            route="/health"
        )

# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejo global de excepciones"""
    return {
        "error": "Error interno del servidor",
        "detail": str(exc),
        "path": str(request.url)
    }

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