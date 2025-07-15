// Interfaces para las respuestas de la API de chat
export interface QuestionRequest {
  question: string;
}

export interface SuccessData {
  answer: string;
  question: string;
  status: 'success';
  confidence: number;
  processing_time_ms: number;
  sources: string[];
  metadata: {
    model_used: string;
    documents_retrieved: number;
    similarity_scores: number[];
  };
}

export interface ErrorData {
  answer: string;
  question: string;
  status: 'validation_error' | 'error';
  confidence: null;
  processing_time_ms: number | null;
  sources: null;
  metadata: null;
}

export interface ApiError {
  field: string;
  type: string;
  message: string;
}

export interface ApiMetadata {
  request_id: string;
  timestamp: string;
  route: string;
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  code: number;
  data: T | null;
  message: string;
  errors: ApiError[];
  metadata: ApiMetadata;
}

export interface PydanticError {
  detail: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

// Tipos de respuesta específicos
export type SuccessResponse = ApiResponse<SuccessData>;
export type ErrorResponse = ApiResponse<ErrorData>;
export type ChatApiResponse = SuccessResponse | ErrorResponse | PydanticError;

// Tipos para la interfaz de usuario
export interface MessageData {
  id: string;
  content: string;
  type: 'user' | 'response';
  timestamp: Date;
}