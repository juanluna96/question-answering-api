"use client";
import { useState } from 'react';
import { VantaBackground } from "@/components/layout/VantaBackground";
import { Title } from "@/components/layout/Title";
import { InputBox } from "@/components/chat/InputBox";
import MessageList from '../components/chat/MessageList';
import { chatService, ChatService } from '../services/chat.service';
import { MessageData } from '../types/chat.types';

export default function Home() {
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (value: string) => {
    const trimmedValue = value.trim();
    if (!trimmedValue || trimmedValue.length < 3) return;

    // Marcar que el usuario ha interactuado
    if (!hasUserInteracted) {
      setHasUserInteracted(true);
    }

    // Agregar mensaje del usuario
    const userMessage: MessageData = {
      id: Date.now().toString(),
      content: trimmedValue,
      type: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Llamada real a la API
      const response = await chatService.askQuestion(trimmedValue);
      
      let responseContent: string;
      let responseSources: string[] | undefined;
      
      if (ChatService.isSuccessResponse(response)) {
        // Respuesta exitosa
        const successData = ChatService.getSuccessData(response);
        responseContent = successData?.answer || 'Respuesta recibida sin contenido';
        responseSources = successData?.sources;
      } else {
        // Error de la API o validación
        responseContent = ChatService.getErrorMessage(response);
      }
      
      const responseMessage: MessageData = {
        id: (Date.now() + 1).toString(),
        content: responseContent,
        type: 'response',
        timestamp: new Date(),
        sources: responseSources
      };
      
      setMessages(prev => [...prev, responseMessage]);
    } catch (error) {
      // Error de conexión
      const errorMessage: MessageData = {
        id: (Date.now() + 1).toString(),
        content: `Error de conexión: ${error instanceof Error ? error.message : 'No se pudo conectar con el servidor'}`,
        type: 'response',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (value: string) => {
    if (value.trim().length > 0 && !hasUserInteracted) {
      setHasUserInteracted(true);
    }
  };

  return (
    <VantaBackground>
      {/* Título centrado */}
      <Title isVisible={!hasUserInteracted}>QuestionAI</Title>
      
      {/* Lista de mensajes cuando hay interacción */}
      {hasUserInteracted && (
          <div className="absolute inset-0 z-20" style={{height: 'calc(100vh - 150px)'}}>
            <div className="h-full overflow-y-auto pt-8">
              <div className="max-w-6xl mx-auto px-4">
                <MessageList messages={messages} isLoading={isLoading} />
              </div>
            </div>
          </div>
        )}
      
     <InputBox 
          onSubmit={handleSubmit}
          onInputChange={handleInputChange}
          isLoading={isLoading}
          placeholder="Escribe tu pregunta aquí..."
          buttonText="Enviar"
        />
    </VantaBackground>
  );
}