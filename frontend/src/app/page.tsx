"use client";
import { useState } from 'react';
import { VantaBackground } from "@/components/layout/VantaBackground";
import { Title } from "@/components/layout/Title";
import { InputBox } from "@/components/chat/InputBox";
import MessageList from '../components/chat/MessageList';

interface MessageData {
  id: string;
  content: string;
  type: 'user' | 'response';
  timestamp: Date;
}

export default function Home() {
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (value: string) => {
    if (!value.trim()) return;

    // Marcar que el usuario ha interactuado
    if (!hasUserInteracted) {
      setHasUserInteracted(true);
    }

    // Agregar mensaje del usuario
    const userMessage: MessageData = {
      id: Date.now().toString(),
      content: value,
      type: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Simular respuesta de la API (reemplazar con llamada real)
    setTimeout(() => {
      const responseMessage: MessageData = {
        id: (Date.now() + 1).toString(),
        content: `Esta es una respuesta simulada a: "${value}". En el futuro, aquí se conectará con la API real.`,
        type: 'response',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, responseMessage]);
      setIsLoading(false);
    }, 1500);
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
          <div className="absolute inset-0 z-20" style={{height: 'calc(100vh - 120px)'}}>
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