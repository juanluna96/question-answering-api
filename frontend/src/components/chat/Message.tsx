"use client";
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import AnimatedStatusText from '../ui/AnimatedStatusText';
import TypeWriterText from '../ui/TypewriterText';

interface MessageProps {
  content: string | React.ReactNode;
  type: 'user' | 'response';
  timestamp?: Date;
  isLoading?: boolean;
  loadingStartTime?: Date;
  sources?: string[];
}

export const Message = ({ content, type, timestamp, isLoading = false, loadingStartTime, sources }: MessageProps) => {
  const isUser = type === 'user';
  const [showFooter, setShowFooter] = useState(isUser || isLoading); // Mostrar inmediatamente para usuarios o cuando está cargando
  
  const handleTypewriterComplete = () => {
    setShowFooter(true);
  };
  
  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}>
      <div className={`min-w-[300px] max-w-xs lg:max-w-md px-4 py-3 rounded-xl ${
        isUser 
          ? 'bg-blue-600 text-white rounded-br-sm' 
          : 'bg-white text-gray-800 rounded-bl-sm border border-gray-200'
      }`}>
        {typeof content === 'string' ? (
          // Usar TypewriterText solo para respuestas que no están cargando
          !isUser && !isLoading ? (
            <TypeWriterText text={content} speed={30} onComplete={handleTypewriterComplete} />
          ) : (
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
            >
              {content}
            </ReactMarkdown>
          )
        ) : (
          content
        )}
        
        {/* Sección de documentos fuente - solo mostrar cuando termine el typewriter */}
        {showFooter && sources && sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200 animate-slide-up">
            <p className="text-xs text-gray-600 mb-2 font-medium">Documentos fuentes:</p>
            <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
              {sources.map((source, index) => (
                <div 
                  key={index}
                  className="flex-shrink-0 bg-blue-50 border border-blue-200 rounded-md px-3 py-1 text-xs text-blue-700 font-medium whitespace-nowrap uppercase"
                >
                  {source}
                </div>
              ))}
            </div>
          </div>
        )}
        {/* Footer con timestamp y status - solo mostrar cuando termine el typewriter */}
          <div className={`flex justify-between items-center text-xs mt-2 ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          } ${
            isLoading && isUser ? 'animate-pulse':''
          } animate-slide-up`}>
            <span>
              {timestamp && 
                timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              }
            </span>
            <AnimatedStatusText 
               isLoading={isLoading && !isUser}
               loadingStartTime={loadingStartTime}
               staticText={isUser ? 'Enviado' : 'Respuesta'}
             />
          </div>
      </div>
    </div>
  );
};

export default Message;