import { configService } from './config.service';
import {
  QuestionRequest,
  SuccessData,
  ErrorData,
  SuccessResponse,
  ErrorResponse,
  ChatApiResponse,
  PydanticError
} from '../types/chat.types';

// Clase del servicio de chat
export class ChatService {
  private readonly endpoint: string;

  constructor() {
    this.endpoint = '/answer';
  }

  /**
   * Envía una pregunta a la API y retorna la respuesta
   */
  async askQuestion(question: string): Promise<ChatApiResponse> {
    try {
      const requestBody: QuestionRequest = { question };
      
      const response = await configService.post<SuccessResponse>(this.endpoint, requestBody);
      
      if (ChatService.isSuccessResponse(response.data)) {
         // Verificar que data no sea null
         if (!response.data.data) {
           throw new Error('Respuesta de la API no contiene datos');
         }
         return response.data;
       } else if (ChatService.isErrorResponse(response.data)) {
         return response.data;
       } else {
         throw new Error('Formato de respuesta no reconocido');
       }
    } catch (error: any) {
      // Si el error tiene respuesta de la API, extraer los datos
      if (error.response?.data) {
        return error.response.data as ErrorResponse | PydanticError;
      }
      
      // Error de red o conexión
      throw new Error(`Error de conexión: ${error.message || 'Error desconocido'}`);
    }
  }

  /**
   * Verifica si la respuesta es exitosa
   */
  static isSuccessResponse(response: ChatApiResponse): response is SuccessResponse {
    return 'status' in response && response.status === 'success';
  }

  /**
   * Verifica si la respuesta es un error de la API
   */
  static isErrorResponse(response: ChatApiResponse): response is ErrorResponse {
    return 'status' in response && response.status === 'error';
  }

  /**
   * Verifica si la respuesta es un error de Pydantic
   */
  static isPydanticError(response: ChatApiResponse): response is PydanticError {
    return 'detail' in response;
  }

  /**
   * Extrae el mensaje de error de cualquier tipo de respuesta de error
   */
  static getErrorMessage(response: ChatApiResponse): string {
    if (this.isErrorResponse(response)) {
      return response.data?.answer || response.message || 'Error desconocido';
    }
    
    if (this.isPydanticError(response)) {
      return response.detail[0]?.msg || 'Error de validación';
    }
    
    return 'Error desconocido';
  }

  /**
   * Extrae la respuesta exitosa
   */
  static getSuccessData(response: ChatApiResponse): SuccessData | null {
    if (this.isSuccessResponse(response)) {
      return response.data;
    }
    return null;
  }
}

// Instancia por defecto del servicio
export const chatService = new ChatService();

// Export por defecto
export default ChatService;