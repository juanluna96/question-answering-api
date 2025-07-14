"use client"

import React, { useState, useEffect } from 'react';

interface TitleProps {
  children: React.ReactNode;
  className?: string;
}

export const Title = ({ children, className = "" }: TitleProps) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <h1 className={`text-black text-8xl font-bold text-center z-10 m-0 transition-all duration-1000 ease-out ${
      isVisible 
        ? 'opacity-100 transform translate-y-0' 
        : 'opacity-0 transform -translate-y-12'
    } ${className}`}>
      {children}
    </h1>
  );
};