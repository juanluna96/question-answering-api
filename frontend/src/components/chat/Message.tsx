"use client";
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageProps {
  content: string | React.ReactNode;
  type: 'user' | 'response';
  timestamp?: Date;
  isLoading?: boolean;
}

export const Message = ({ content, type, timestamp, isLoading = false }: MessageProps) => {
  const isUser = type === 'user';
  
  const getStatusText = () => {
    if (isUser) {
      return 'Enviado';
    } else {
      return isLoading ? 'Pensando...' : 'Respondido';
    }
  };
  
  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}>
      <div className={`min-w-[300px] max-w-xs lg:max-w-md px-4 py-3 rounded-xl ${
        isUser 
          ? 'bg-blue-600 text-white rounded-br-sm' 
          : 'bg-white text-gray-800 rounded-bl-sm border border-gray-200'
      }`}>
        {typeof content === 'string' ? (
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
          >
            {content}
          </ReactMarkdown>
        ) : (
          content
        )}
        <div className={`flex justify-between items-center text-xs mt-2 ${
          isUser ? 'text-blue-100' : 'text-gray-500'
        } ${
          isLoading && isUser ? 'animate-pulse':''
        }`}>
          <span>
            {timestamp && 
              timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
          </span>
          <span>
            {getStatusText()}
          </span>
        </div>
      </div>
    </div>
  );
};

export default Message;