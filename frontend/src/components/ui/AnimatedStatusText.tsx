"use client";
import React, { useState, useEffect } from 'react';

interface AnimatedStatusTextProps {
  isLoading: boolean;
  loadingStartTime?: Date;
  staticText?: string;
}

const AnimatedDots = () => (
  <span className="ml-1">
    <span className="animate-bounce inline-block" style={{ animationDelay: '0ms', animationDuration: '1s' }}>.</span>
    <span className="animate-bounce inline-block" style={{ animationDelay: '200ms', animationDuration: '1s' }}>.</span>
    <span className="animate-bounce inline-block" style={{ animationDelay: '400ms', animationDuration: '1s' }}>.</span>
  </span>
);

export const AnimatedStatusText = ({ 
  isLoading, 
  loadingStartTime, 
  staticText = 'Completado' 
}: AnimatedStatusTextProps) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  
  useEffect(() => {
    if (isLoading && loadingStartTime) {
      const interval = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now.getTime() - loadingStartTime.getTime()) / 1000);
        setElapsedSeconds(elapsed);
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [isLoading, loadingStartTime]);
  
  const getStatusText = () => {
    if (!isLoading) {
      return staticText;
    }
    
    if (elapsedSeconds < 3) {
      return 'Pensando';
    } else if (elapsedSeconds < 6) {
      return 'Estoy en ello';
    } else if (elapsedSeconds < 10) {
      return 'Ya casi';
    } else {
      return 'Un momento más';
    }
  };
  
  const getStatusContent = () => {
    if (!isLoading) {
      return staticText;
    }
    
    return (
      <span className="inline-flex items-center">
        <span className="transition-all duration-500 ease-in-out">
          {getStatusText()}
        </span>
        <AnimatedDots />
      </span>
    );
  };
  
  return (
    <div className="transition-opacity duration-300 ease-in-out">
      {getStatusContent()}
    </div>
  );
};

export default AnimatedStatusText;