from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, validator
import os
from .infrastructure.config.dependency_container import DependencyContainer

# Instancia global del contenedor de dependencias
dependency_container = DependencyContainer()

# Modelos de request y response
class QuestionRequest(BaseModel):
    question: str = Field(..., description="Pregunta a responder")
    
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
    
class AnswerResponse(BaseModel):
    answer: str
    question: str
    status: str

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
    title="Question Answering API",
    description="API para generar embeddings y responder preguntas basadas en documentos CSV",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas eliminadas - solo mantenemos endpoints básicos

# Ruta raíz
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Question Answering API",
        "version": "1.0.0",
        "description": "API para generar embeddings y responder preguntas",
        "endpoints": {
            "answer": "/answer",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# Endpoint principal para responder preguntas
@app.post("/answer", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest) -> AnswerResponse:
    """Endpoint principal para procesar preguntas y generar respuestas
    
    Args:
        request: Solicitud con la pregunta
        
    Returns:
        Respuesta generada
        
    Raises:
        HTTPException: Si hay error en el procesamiento
    """
    try:
        # Por ahora, una respuesta simple de ejemplo
        # Aquí se implementaría la lógica de question-answering
        answer = f"Esta es una respuesta de ejemplo para la pregunta: {request.question}"
        
        return AnswerResponse(
            answer=answer,
            question=request.question,
            status="success"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la pregunta: {str(e)}"
        )

# Health check global
@app.get("/health")
async def health_check():
    """Health check global de la aplicación"""
    try:
        config = dependency_container.get_config()
        
        return {
            "status": "healthy",
            "service": "question-answering-api",
            "version": "1.0.0",
            "config": {
                "openai_configured": bool(config.get("openai_api_key")),
                "model": config.get("openai_model"),
                "cache_path": config.get("default_cache_path")
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en health check: {str(e)}"
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