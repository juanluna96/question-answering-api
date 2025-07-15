from fastapi import APIRouter, HTTPException, Depends
from ...application.dto.question_dto import QuestionRequestDTO, AnswerResponseDTO
from ...application.use_cases.answer_question_use_case import AnswerQuestionUseCase
from ...application.services.question_service_factory import QuestionServiceFactory
from ...domain.ports.question_service_port import QuestionServicePort
from ...infrastructure.config.settings import Settings
from .response_models import StandardResponse, create_success_response, create_error_response

class QuestionController:
    """Controlador para endpoints relacionados con preguntas"""
    
    def __init__(self):
        self._router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas del controlador"""
        
        @self._router.post(
            "/answer",
            response_model=StandardResponse,
            summary="Procesar pregunta",
            description="Recibe una pregunta y retorna una respuesta procesada",
            tags=["Questions"]
        )
        async def answer_question(
            request: QuestionRequestDTO,
            use_case: AnswerQuestionUseCase = Depends(self._get_answer_use_case)
        ) -> StandardResponse:
            """
            Endpoint para procesar preguntas y generar respuestas
            
            Args:
                request: DTO con la pregunta a procesar
                use_case: Caso de uso inyectado
                
            Returns:
                StandardResponse: Respuesta procesada en formato estándar
                
            Raises:
                HTTPException: Si hay error en el procesamiento
            """
            try:
                result = await use_case.execute(request)
                
                # Si el status es error, retornar error estándar
                if result.status == "error" and "Error:" in result.answer:
                    return create_error_response(
                        code=400,
                        message="Error en la validación de la pregunta",
                        errors=[{"field": "question", "type": "Validation Error", "message": result.answer}],
                        route="/answer",
                        data=result.dict()
                    )
                
                # Retornar respuesta exitosa estándar
                return create_success_response(
                    data=result.dict(),
                    message="Pregunta procesada exitosamente",
                    route="/answer"
                )
                
            except HTTPException as e:
                return create_error_response(
                    code=e.status_code,
                    message=str(e.detail),
                    errors=[{"field": "general", "type": "HTTP Error", "message": str(e.detail)}],
                    route="/answer"
                )
            except Exception as e:
                return create_error_response(
                    code=500,
                    message="Error interno del servidor",
                    errors=[{"field": "general", "type": "Internal Error", "message": str(e)}],
                    route="/answer"
                )
    
    async def _get_answer_use_case(self) -> AnswerQuestionUseCase:
        """
        Factory method para crear el caso de uso
        Usa el factory para crear el servicio RAG apropiado
        """
        settings = Settings()
        factory = QuestionServiceFactory(settings)
        question_service = await factory.create_question_service(use_rag=True)
        return AnswerQuestionUseCase(question_service)
    
    def get_router(self) -> APIRouter:
        """Retorna el router configurado"""
        return self._router