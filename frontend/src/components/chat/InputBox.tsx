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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && onSubmit && !isLoading) {
      onSubmit(inputValue.trim());
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
    // Notificar el cambio del input
    if (onInputChange) {
      onInputChange(value);
    }
  };

  return (
    <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-6xl px-4">
      <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder={placeholder}
            disabled={isLoading}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-800 placeholder-gray-500 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:border-gray-200 disabled:text-gray-500"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {isLoading ? "Enviando..." : buttonText}
          </button>
        </form>
      </div>
    </div>
  );
};