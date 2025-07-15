"use client";
import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface TypewriterTextProps {
  text: string;
  speed?: number; // velocidad en milisegundos por palabra
  onComplete?: () => void;
}

const TypeWriterText: React.FC<TypewriterTextProps> = ({ 
  text, 
  speed = 100, 
  onComplete 
}) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  // Dividir el texto en palabras manteniendo espacios y saltos de línea
  const words = text.split(/( |\n)/);

  useEffect(() => {
    if (currentWordIndex < words.length && !isComplete) {
      const timer = setTimeout(() => {
        setDisplayedText(prev => prev + words[currentWordIndex]);
        setCurrentWordIndex(prev => prev + 1);
      }, speed);

      return () => clearTimeout(timer);
    } else if (currentWordIndex >= words.length && !isComplete) {
      setIsComplete(true);
      onComplete?.();
    }
  }, [currentWordIndex, words, speed, onComplete, isComplete]);

  // Reset cuando cambia el texto
  useEffect(() => {
    setDisplayedText('');
    setCurrentWordIndex(0);
    setIsComplete(false);
  }, [text]);

  return (
    <div className="relative">
      <div className="inline">
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <span>{children}</span>,
            // Mantener otros elementos como inline cuando sea posible
          }}
        >
          {displayedText}
        </ReactMarkdown>
        {!isComplete && (
          <span className="animate-pulse text-gray-400 ml-1">|</span>
        )}
      </div>
    </div>
  );
};

export default TypeWriterText;