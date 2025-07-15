"use client";
import React from 'react';
import Message from './Message';
import { LoadingSkeletonText } from '../ui/LoadingSkeletonText';

interface MessageData {
  id: string;
  content: string;
  type: 'user' | 'response';
  timestamp: Date;
}

interface MessageListProps {
  messages: MessageData[];
  isLoading?: boolean;
}

export const MessageList = ({ messages, isLoading }: MessageListProps) => {
  const TitleChat = messages.length > 0 ? 'Historial de conversaciones': 'Escribe tu pregunta para comenzar la conversación'
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        <div className="flex items-center justify-center h-full">
          <h2 className="text-gray-500 text-center text-2xl">
            {TitleChat}
          </h2>
        </div>
        {messages.map((message, index) => {
           const isLastMessage = index === messages.length - 1;
           return (
             <Message
               key={message.id}
               content={message.content}
               type={message.type}
               timestamp={message.timestamp}
               isLoading={isLoading && isLastMessage && message.type === 'user'}
             />
           );
         })}
        {isLoading && (
          <Message
            key="loading"
            content={
              <LoadingSkeletonText />
            }
            type="response"
            isLoading={true}
            timestamp={new Date()}
          />
        )}
    </div>
  );
};

export default MessageList;