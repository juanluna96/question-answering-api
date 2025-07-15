"use client";
import React, { useState } from 'react';

interface InputBoxProps {
  onSubmit?: (value: string) => void;
  onInputChange?: (value: string) => void;
  placeholder?: string;
  buttonText?: string;
  isLoading?: boolean;
}

export const InputBox = ({ 
  onSubmit, 
  onInputChange,
  placeholder = "Escribe tu pregunta...", 
  buttonText = "Enviar",
  isLoading = false
}: InputBoxProps) => {
  const [inputValue, setInputValue] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedValue = inputValue.trim();
    
    // Limpiar error previo
    setErrorMessage('');
    
    if (!trimmedValue) {
      setErrorMessage('El mensaje no puede estar vacío');
      return;
    }
    
    if (trimmedValue.length < 3) {
      setErrorMessage('El mensaje debe tener al menos 3 caracteres');
      return;
    }
    
    if (onSubmit && !isLoading) {
      onSubmit(trimmedValue);
      setInputValue('');
      // Notificar que el input está vacío después del envío
      if (onInputChange) {
        onInputChange('');
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);
    
    // Limpiar mensaje de error cuando el usuario empiece a escribir
    if (errorMessage) {
      setErrorMessage('');
    }
    
    // Notificar el cambio del input
    if (onInputChange) {
      onInputChange(value);
    }
  };

  return (
    <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-6xl px-4">
      {errorMessage && (
          <div className="mb-2 bg-red-50 border border-red-200 rounded-t-xl px-4 py-2 shadow-sm animate-slide-down">
            <div className="flex items-center justify-between">
              <div className="text-sm text-red-600 font-medium">
                {errorMessage}
              </div>
              <button
                onClick={() => setErrorMessage('')}
                className="ml-2 text-red-400 hover:text-red-600 transition-colors duration-200 focus:outline-none"
                aria-label="Cerrar mensaje de error"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}
      <div className={`bg-white/90 backdrop-blur-sm shadow-lg border border-gray-200 p-4 ${
        errorMessage ? 'rounded-b-2xl rounded-t-none border-t-0' : 'rounded-2xl'
      }`}>
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder={placeholder}
            disabled={isLoading}
            className={`flex-1 px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:border-transparent text-gray-800 placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:border-gray-200 disabled:text-gray-500 ${
              errorMessage 
                ? 'border-red-300 focus:ring-red-500' 
                : 'border-gray-300 focus:ring-blue-500'
            }`}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {isLoading ? "Enviando..." : buttonText}
          </button>
        </form>
      </div>
    </div>
  );
};