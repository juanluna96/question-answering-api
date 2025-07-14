"use client"

import React, { useState, useEffect } from 'react';

interface TitleProps {
  children: React.ReactNode;
  className?: string;
  isVisible?: boolean;
}

export const Title = ({ children, className = "", isVisible = true }: TitleProps) => {
  const shouldBeVisible = isVisible;

  return (
    <h1 className={`text-black text-8xl font-bold text-center z-10 m-0 transition-all duration-1000 ease-out ${
      shouldBeVisible 
        ? 'opacity-100 transform translate-y-0' 
        : 'opacity-0 transform -translate-y-12'
    } ${className}`}>
      {children}
    </h1>
  );
};