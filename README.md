# Question Answering API

Sistema completo de preguntas y respuestas basado en embeddings de documentos CSV, implementado con arquitectura hexagonal en el backend y una interfaz moderna en el frontend.

## 🏗️ Arquitectura del Proyecto

Este proyecto está dividido en dos componentes principales:

### 📊 Backend (FastAPI)
- **Ubicación**: `/backend/`
- **Tecnología**: FastAPI con Python
- **Arquitectura**: Hexagonal (Ports & Adapters)
- **Funcionalidad**: API REST para generar embeddings y responder preguntas

### 🎨 Frontend (Next.js)
- **Ubicación**: `/frontend/`
- **Tecnología**: Next.js 14 con TypeScript y Tailwind CSS
- **Funcionalidad**: Interfaz de usuario moderna para interactuar con la API

## 🚀 Inicio Rápido

### Con Docker (Recomendado)

```bash
# Clonar el repositorio
git clone <repository-url>
cd question-answering-api

# Ejecutar todo el stack
docker-compose up
```

**URLs de acceso:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Documentación API: http://localhost:8000/docs

### Sin Docker

#### Backend
```bash
cd backend/

# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu OPENAI_API_KEY

# Ejecutar servidor
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend/

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con la URL del backend

# Ejecutar en desarrollo
npm run dev
```

## 📁 Estructura del Proyecto

```
question-answering-api/
├── backend/                    # API REST con FastAPI
│   ├── app/
│   │   ├── domain/            # Entidades y puertos (núcleo del negocio)
│   │   ├── application/       # Casos de uso y DTOs
│   │   ├── infrastructure/    # Adaptadores externos
│   │   └── main.py           # Punto de entrada de la aplicación
│   ├── tests/                # Tests unitarios y de integración
│   ├── requirements.txt      # Dependencias de Python
│   ├── Dockerfile           # Imagen Docker del backend
│   └── README.md            # Documentación específica del backend
├── frontend/                  # Interfaz de usuario con Next.js
│   ├── src/
│   │   ├── app/              # App Router de Next.js
│   │   ├── components/       # Componentes reutilizables
│   │   ├── services/         # Servicios para comunicación con API
│   │   └── types/           # Definiciones de tipos TypeScript
│   ├── package.json         # Dependencias de Node.js
│   ├── Dockerfile          # Imagen Docker del frontend
│   └── README.md           # Documentación específica del frontend
├── docker-compose.yml       # Orquestación de servicios
└── README.md               # Este archivo
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno y rápido
- **OpenAI API** - Generación de embeddings y respuestas
- **Pandas** - Procesamiento de datos CSV
- **Uvicorn** - Servidor ASGI
- **Pytest** - Framework de testing
- **Docker** - Containerización

### Frontend
- **Next.js 14** - Framework de React con App Router
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Framework de CSS utilitario
- **React** - Biblioteca de interfaz de usuario
- **Docker** - Containerización

## 🔧 Configuración

### Variables de Entorno

#### Backend (.env)
```env
OPENAI_API_KEY=tu_api_key_aqui
ENVIRONMENT=development
DEBUG=true
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📚 Documentación Detallada

Para información más específica sobre cada componente:

- **Backend**: Ver [backend/README.md](./backend/README.md)
  - Arquitectura hexagonal detallada
  - Casos de uso y endpoints
  - Configuración de desarrollo
  - Estrategias de testing

- **Frontend**: Ver [frontend/README.md](./frontend/README.md)
  - Estructura de componentes
  - Configuración de Tailwind CSS
  - Scripts de desarrollo
  - Configuración de Docker

## 🧪 Testing

### Backend
```bash
cd backend/
pytest tests/ -v
```

### Frontend
```bash
cd frontend/
npm test
```

## 🐳 Docker

El proyecto incluye configuración completa de Docker con:
- Multi-stage builds para optimización
- Hot reload en desarrollo
- Volúmenes optimizados
- Network compartida entre servicios