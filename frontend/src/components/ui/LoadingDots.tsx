"use client";
import React from 'react';

export const LoadingDots = () => {
  return (
    <div className="flex justify-start">
      <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 border border-gray-200">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse-scale"></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse-scale" style={{animationDelay: '0.2s'}}></div>
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse-scale" style={{animationDelay: '0.4s'}}></div>
        </div>
      </div>
    </div>
  );
};

export default LoadingDots;