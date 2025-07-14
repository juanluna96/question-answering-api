"use client";
import React from 'react';

interface MessageProps {
  content: string;
  type: 'user' | 'response';
  timestamp?: Date;
}

export const Message = ({ content, type, timestamp }: MessageProps) => {
  const isUser = type === 'user';
  
  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}>
      <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-xl ${
        isUser 
          ? 'bg-blue-600 text-white rounded-br-sm' 
          : 'bg-white text-gray-800 rounded-bl-sm border border-gray-200'
      }`}>
        <p className="text-sm leading-relaxed">{content}</p>
        {timestamp && (
          <p className={`text-xs mt-1 ${
            isUser ? 'text-blue-100' : 'text-gray-500'
          }`}>
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  );
};

export default Message;