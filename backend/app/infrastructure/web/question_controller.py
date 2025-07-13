from fastapi import APIRouter, HTTPException, Depends
from ...application.dto.question_dto import QuestionRequestDTO, AnswerResponseDTO
from ...application.use_cases.answer_question_use_case import AnswerQuestionUseCase
from ...domain.ports.question_service_port import QuestionServicePort
from ..services.simple_question_service import SimpleQuestionService

class QuestionController:
    """Controlador para endpoints relacionados con preguntas"""
    
    def __init__(self):
        self._router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas del controlador"""
        
        @self._router.post(
            "/answer",
            response_model=AnswerResponseDTO,
            summary="Procesar pregunta",
            description="Recibe una pregunta y retorna una respuesta procesada",
            tags=["Questions"]
        )
        async def answer_question(
            request: QuestionRequestDTO,
            use_case: AnswerQuestionUseCase = Depends(self._get_answer_use_case)
        ) -> AnswerResponseDTO:
            """
            Endpoint para procesar preguntas y generar respuestas
            
            Args:
                request: DTO con la pregunta a procesar
                use_case: Caso de uso inyectado
                
            Returns:
                AnswerResponseDTO: Respuesta procesada
                
            Raises:
                HTTPException: Si hay error en el procesamiento
            """
            try:
                result = await use_case.execute(request)
                
                # Si el status es error, retornar 400
                if result.status == "error" and "Error:" in result.answer:
                    raise HTTPException(
                        status_code=400,
                        detail=result.answer
                    )
                
                return result
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error interno del servidor: {str(e)}"
                )
    
    def _get_answer_use_case(self) -> AnswerQuestionUseCase:
        """
        Factory method para crear el caso de uso
        En una implementación real, esto vendría del contenedor de dependencias
        """
        question_service = SimpleQuestionService()
        return AnswerQuestionUseCase(question_service)
    
    def get_router(self) -> APIRouter:
        """Retorna el router configurado"""
        return self._router