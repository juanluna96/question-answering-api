"use client";
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import AnimatedStatusText from '../ui/AnimatedStatusText';

interface MessageProps {
  content: string | React.ReactNode;
  type: 'user' | 'response';
  timestamp?: Date;
  isLoading?: boolean;
  loadingStartTime?: Date;
}

export const Message = ({ content, type, timestamp, isLoading = false, loadingStartTime }: MessageProps) => {
  const isUser = type === 'user';
  
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
          <AnimatedStatusText 
             isLoading={isLoading && !isUser}
             loadingStartTime={loadingStartTime}
             staticText={isUser ? 'Enviado' : 'Respondido'}
           />
        </div>
      </div>
    </div>
  );
};

export default Message;