"use client";

import React, { useState, useEffect, useRef } from "react";
import * as THREE from "three";

export const VantaBackground = () => {
  const [vantaEffect, setVantaEffect] = useState(0);
  const vantaRef = useRef(null);

  useEffect(() => {
    // Expose THREE globally for Vanta compatibility
    (window as any).THREE = THREE;
    
    // Load DOTS from CDN
    const loadDOTS = () => {
      return new Promise((resolve) => {
        if ((window as any).VANTA && (window as any).VANTA.DOTS) {
          console.log('DOTS already loaded');
          resolve((window as any).VANTA.DOTS);
          return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/vanta/0.5.24/vanta.dots.min.js';
        script.onload = () => {
          console.log('DOTS loaded from CDN:', (window as any).VANTA?.DOTS);
          resolve((window as any).VANTA?.DOTS);
        };
        script.onerror = () => {
          console.error('Failed to load DOTS from CDN');
          resolve(null);
        };
        document.head.appendChild(script);
      });
    };
    
    const initVanta = async () => {
      if (!vantaEffect && vantaRef.current) {
        const DOTS = await loadDOTS();
        
        if (!DOTS) {
          console.error('DOTS failed to load');
          return;
        }
        
        try {
          console.log('Initializing Vanta DOTS with THREE:', THREE);
          setVantaEffect(
            DOTS({
              el: vantaRef.current,
              THREE: THREE,
              minHeight: 600.0,
              minWidth: 600.0,
              scale: 1.0,
              scaleMobile: 1.0,
              color: 0x2088ff,
              backgroundColor: 0xffffff,
              size: 3.0,
              showLines: false
            })
          );
        } catch (error) {
          console.error("Error initializing Vanta:", error);
        }
      }
    };
    
    initVanta();
    
    return () => {
      if (vantaEffect) vantaEffect.destroy();
    };
  }, [vantaEffect]);
  
  return (
    <div ref={vantaRef} style={{ height: "100vh" }}>
      <p style={{ color: "#fff", paddingTop: "20px" }}>
        Animated website backgrounds in a few lines of code.
      </p>
    </div>
  );
};