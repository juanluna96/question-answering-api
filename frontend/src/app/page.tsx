"use client";
import { VantaBackground } from "@/components/VantaBackground";
import { Title } from "@/components/Title";
import { InputBox } from "@/components/InputBox";
import { useState } from "react";

export default function Home() {
  const [hasUserInteracted, setHasUserInteracted] = useState(false);

  const handleSubmit = (value: string) => {
    console.log('Pregunta enviada:', value);
    // Aquí se puede agregar la lógica para enviar la pregunta al backend
  };

  const handleInputChange = (value: string) => {
    // Marcar que el usuario ha interactuado en cuanto escriba algo
    if (value.trim().length > 0 && !hasUserInteracted) {
      setHasUserInteracted(true);
    }
  };

  return (
    <VantaBackground>
      <Title isVisible={!hasUserInteracted}>
        QuestionAI
      </Title>
      <InputBox 
        onSubmit={handleSubmit}
        onInputChange={handleInputChange}
        placeholder="Haz tu pregunta a QuestionAI..."
        buttonText="Preguntar"
      />
    </VantaBackground>
  )
}