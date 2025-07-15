# Question Answering API - Backend

API REST para generar embeddings de documentos CSV y responder preguntas basadas en el contenido, implementada con **Arquitectura Hexagonal** (Ports & Adapters).

## 🏗️ Arquitectura

Este proyecto implementa una arquitectura hexagonal que separa claramente las responsabilidades:

```
app/
├── domain/                 # Núcleo del negocio
│   ├── entities/          # Entidades de dominio
│   ├── ports/             # Interfaces (contratos)
│   └── services/          # Servicios de dominio
├── application/           # Casos de uso
│   ├── dto/              # Data Transfer Objects
│   └── use_cases/        # Lógica de aplicación
└── infrastructure/        # Adaptadores externos
    ├── repositories/      # Implementaciones de repositorios
    ├── services/         # Implementaciones de servicios
    ├── web/              # Controladores HTTP
    └── config/           # Configuración e inyección de dependencias
```

### Capas de la Arquitectura

#### 🎯 **Dominio** (`app/domain/`)
- **Entidades**: `Document`, `DocumentEmbedding` - Modelos de negocio puros
- **Puertos**: Interfaces que definen contratos (`DocumentRepository`, `EmbeddingService`, `CacheService`)
- **Servicios**: `EmbeddingManager` - Orquesta la lógica de negocio

#### 🔄 **Aplicación** (`app/application/`)
- **DTOs**: Objetos para transferencia de datos entre capas
- **Casos de Uso**: `LoadEmbeddingsUseCase`, `GetCacheStatusUseCase` - Lógica específica de la aplicación

#### 🔌 **Infraestructura** (`app/infrastructure/`)
- **Repositorios**: `CSVDocumentRepository` - Carga documentos desde CSV usando pandas
- **Servicios**: `OpenAIEmbeddingService`, `PickleCacheService` - Implementaciones concretas
- **Web**: `EmbeddingController` - Controladores HTTP con FastAPI
- **Configuración**: `DependencyContainer` - Inyección de dependencias

## 🚀 Instalación y Configuración

### Opción 1: Con Docker (Recomendado para desarrollo)

#### 1. Configurar variables de entorno

Copia el archivo de ejemplo y configura tus variables:

```bash
cp .env.example .env
```

Edita `.env` con tus configuraciones:

```env
OPENAI_API_KEY=tu_api_key_de_openai
OPENAI_MODEL=text-embedding-3-small
DEFAULT_CACHE_PATH=./data/cache/embeddings.pkl
MAX_FILE_SIZE_MB=50
BATCH_SIZE=100
DOCUMENTS_CSV_PATH=./data/documents.csv
```

#### 2. Ejecutar con Docker Compose

```bash
# Construir y ejecutar en modo desarrollo
docker-compose up --build

# Ejecutar en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

#### 3. Comandos útiles de Docker

```bash
# Reconstruir imagen
docker-compose build --no-cache

# Ejecutar comandos dentro del contenedor
docker-compose exec question-answering-api bash

# Ver estado de servicios
docker-compose ps

# Limpiar volúmenes (cuidado: elimina datos)
docker-compose down -v
```

### Opción 2: Instalación Local

#### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 2. Configurar variables de entorno

Sigue el mismo proceso que en la opción Docker.

#### 3. Crear directorios necesarios

```bash
mkdir -p data/
mkdir -p data/cache
```

## 🏃‍♂️ Ejecución

### Con Docker

```bash
# Desarrollo con hot-reload
docker-compose up
```

### Sin Docker

#### Desarrollo

```bash
# Desde el directorio backend/
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Producción

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔗 Endpoints Principales

### 1. Procesar Pregunta

```http
POST /answer
Content-Type: application/json

{
  "question": "¿Cuál es el proceso para solicitar una licencia?"
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Pregunta procesada exitosamente",
  "data": {
    "answer": "Para solicitar una licencia, debe seguir los siguientes pasos...",
    "sources": ["doc_001", "doc_015", "doc_032"]
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "route": "/answer"
}
```

### 2. Información de la API

```http
GET /
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Información de la API obtenida exitosamente",
  "data": {
    "name": "Question Answering API",
    "version": "1.0.0",
    "description": "API para procesamiento de preguntas y respuestas",
    "endpoints": {
      "/": "Información de la API",
      "/health": "Estado de salud de la API",
      "/docs": "Documentación interactiva (Swagger UI)",
      "/redoc": "Documentación alternativa (ReDoc)",
      "/answer": "Procesar pregunta (POST)"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "route": "/"
}
```

### 3. Health Check

```http
GET /health
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Servicio funcionando correctamente",
  "data": {
    "status": "healthy",
    "service": "question-answering-api",
    "version": "1.0.0",
    "config": {
      "openai_configured": true,
      "model": "text-embedding-3-small",
      "cache_path": "./data/cache/embeddings.pkl"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "route": "/health"
}
```

### 4. Documentación Interactiva

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

> **Nota**: Los endpoints de embeddings (`/embeddings/*`) están implementados pero no están actualmente incluidos en la aplicación principal. Si necesitas usar funcionalidades de carga de embeddings, contacta al equipo de desarrollo.

## 📁 Formato del CSV

El sistema acepta archivos CSV con las siguientes características:

- **Procesamiento con pandas**: Utiliza pandas para un procesamiento robusto y eficiente
- **Detección automática de separadores**: pandas detecta automáticamente delimitadores
- **Múltiples encodings**: Soporta UTF-8, Latin-1, CP1252, ISO-8859-1
- **Columnas de contenido**: Busca automáticamente columnas con nombres como:
  - `content`, `text`, `description`, `body`, `message`, `document`, `texto`, `contenido`
  - Si no encuentra estas columnas, usa la columna con más texto promedio
- **Limpieza automática**: Elimina filas vacías y limpia espacios en blanco
- **Metadatos**: Todas las demás columnas se guardan como metadatos
- **Validación de tamaño**: Controla el tamaño máximo de archivo (configurable)

Ejemplos de estructuras soportadas:

```csv
id,content,category
1,"Este es el contenido del documento...","FAQ"
2,"Otro documento con información...","Manual"
```

```csv
title,description,tags
"Título 1","Descripción detallada del tema...","tag1,tag2"
"Título 2","Otra descripción importante...","tag3,tag4"
```

## 🐳 Docker

### Ventajas del desarrollo con Docker

- **Entorno consistente**: Mismo entorno en desarrollo, testing y producción
- **Fácil setup**: Un solo comando para levantar toda la aplicación
- **Aislamiento**: No interfiere con otras aplicaciones o versiones de Python
- **Hot-reload**: Los cambios en el código se reflejan automáticamente
- **Persistencia de datos**: Los datos y cache se mantienen entre reinicios

### Estructura de archivos Docker

```
backend/
├── Dockerfile              # Imagen de la aplicación
├── docker-compose.yml      # Orquestación de servicios
├── .dockerignore          # Archivos excluidos del build
└── .env                   # Variables de entorno
```

### Volúmenes y persistencia

El docker-compose está configurado con volúmenes para:

- **Código fuente**: Montado para hot-reload (`./:/app`)
- **Datos**: Persistencia de cache y uploads (`./data:/app/data`)

### Variables de entorno en Docker

El contenedor lee automáticamente el archivo `.env`. Asegúrate de configurar:

```env
# Requerido
OPENAI_API_KEY=tu_api_key_aqui

# Opcional (con valores por defecto)
OPENAI_MODEL=text-embedding-3-small
DEFAULT_CACHE_PATH=./data/cache/embeddings.pkl
DOCUMENTS_CSV_PATH=./data/documents.csv
MAX_FILE_SIZE_MB=50
BATCH_SIZE=100
```

## 🧪 Testing

El proyecto incluye una suite completa de tests que cubren todos los casos de uso y componentes principales.

### Estructura de Tests

```
tests/
├── __init__.py
├── conftest.py                              # Configuración y fixtures compartidos
└── use_cases/
    ├── __init__.py
    ├── test_answer_question_use_case.py      # Tests del caso de uso básico
    ├── test_enhanced_answer_question_use_case.py  # Tests del caso de uso mejorado
    └── test_load_embeddings_use_case.py      # Tests de carga de embeddings
```

### Cobertura de Tests

#### 📝 **test_answer_question_use_case.py** (17 tests)
- ✅ Procesamiento exitoso de preguntas
- ✅ Manejo de errores de validación
- ✅ Manejo de errores de procesamiento
- ✅ Cálculo correcto de tiempos de procesamiento
- ✅ Lógica condicional de fuentes (sources)
- ✅ Reintentos automáticos en caso de error
- ✅ Validación de entrada y respuesta

#### 🚀 **test_enhanced_answer_question_use_case.py** (13 tests)
- ✅ Metadatos completos del proceso RAG
- ✅ Información de debug (desarrollo)
- ✅ Estadísticas del servicio RAG
- ✅ Manejo de errores con reintentos
- ✅ Análisis de preguntas y respuestas
- ✅ Tiempos de procesamiento detallados
- ✅ Detección automática de servicios RAG vs básicos
- ✅ Manejo de errores en estadísticas del servicio

#### 📊 **test_load_embeddings_use_case.py** (12 tests)
- ✅ Carga exitosa de embeddings desde CSV
- ✅ Validación de archivos CSV
- ✅ Manejo de errores de archivo
- ✅ Estado del cache de embeddings
- ✅ Gestión de memoria y recursos
- ✅ Procesamiento por lotes (batching)

### Ejecutar Tests

#### Con Docker (Recomendado)

```bash
# Ejecutar todos los tests
docker-compose exec question-answering-api pytest

# Ejecutar tests con verbose output
docker-compose exec question-answering-api pytest -v

# Ejecutar tests de un archivo específico
docker-compose exec question-answering-api pytest tests/use_cases/test_answer_question_use_case.py

# Ejecutar un test específico
docker-compose exec question-answering-api pytest tests/use_cases/test_answer_question_use_case.py::TestAnswerQuestionUseCase::test_execute_success

# Ejecutar tests con coverage
docker-compose exec question-answering-api pytest --cov=app

# Generar reporte HTML de coverage
docker-compose exec question-answering-api pytest --cov=app --cov-report=html
```

#### Sin Docker

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx pytest-cov

# Ejecutar todos los tests
pytest

# Ejecutar tests con verbose output
pytest -v

# Ejecutar tests con coverage
pytest --cov=app

# Ejecutar tests en paralelo (más rápido)
pip install pytest-xdist
pytest -n auto
```

### Configuración de Tests

Los tests están configurados en `pytest.ini`:

```ini
[tool:pytest]
addopts = -v --tb=short
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

### Fixtures y Mocks

El archivo `conftest.py` proporciona fixtures reutilizables:

- **`sample_question_request`**: DTO de pregunta de ejemplo
- **`mock_question_service`**: Mock del servicio básico de preguntas
- **`mock_rag_service`**: Mock del servicio RAG con estadísticas
- **`enhanced_use_case`**: Instancia del caso de uso mejorado
- **`mock_embedding_service`**: Mock del servicio de embeddings
- **`mock_cache_service`**: Mock del servicio de cache

### Tipos de Tests

#### 🎯 **Tests Unitarios**
- Cada caso de uso se prueba de forma aislada
- Uso extensivo de mocks para dependencias externas
- Verificación de lógica de negocio específica

#### 🔄 **Tests de Integración**
- Interacción entre múltiples componentes
- Flujos completos de procesamiento
- Manejo de errores end-to-end

#### ⚡ **Tests Asíncronos**
- Todos los casos de uso son asíncronos
- Uso de `pytest-asyncio` para manejo correcto
- Simulación de operaciones de I/O

### Estrategias de Testing

#### 📊 **Casos de Éxito**
- Procesamiento normal de preguntas
- Generación correcta de respuestas
- Metadatos completos y precisos

#### ❌ **Casos de Error**
- Validación de entrada inválida
- Errores de servicios externos
- Timeouts y problemas de conectividad
- Reintentos automáticos

#### 🔍 **Casos Edge**
- Preguntas muy cortas o muy largas
- Respuestas genéricas vs específicas
- Servicios RAG vs servicios básicos
- Cache hits vs cache misses

### Métricas de Calidad

```bash
# Ver estadísticas de tests
pytest --tb=no -q

# Resultado esperado:
# 42 passed, 3 warnings in 0.98s
```

#### Cobertura de Código
- **Objetivo**: >90% de cobertura
- **Áreas críticas**: 100% en casos de uso
- **Exclusiones**: Configuración y archivos de infraestructura

### Debugging Tests

```bash
# Ejecutar tests con output detallado
pytest -s -vv

# Ejecutar tests con pdb en fallos
pytest --pdb

# Ejecutar solo tests que fallaron la última vez
pytest --lf

# Ejecutar tests hasta el primer fallo
pytest -x
```

### CI/CD Integration

Los tests están diseñados para integrarse fácilmente en pipelines de CI/CD:

```bash
# Comando típico para CI
pytest --cov=app --cov-report=xml --junitxml=test-results.xml
```

### Buenas Prácticas

1. **Aislamiento**: Cada test es independiente
2. **Determinismo**: Los tests producen resultados consistentes
3. **Velocidad**: Uso de mocks para operaciones costosas
4. **Claridad**: Nombres descriptivos y documentación
5. **Mantenibilidad**: Fixtures reutilizables y código DRY

## 🔧 Configuración Avanzada

### Modelos de OpenAI Soportados

- `text-embedding-3-small` (1536 dimensiones) - Recomendado
- `text-embedding-3-large` (3072 dimensiones)
- `text-embedding-ada-002` (1536 dimensiones) - Legacy

### Límites y Consideraciones

- **Tamaño máximo de archivo**: Configurable via `MAX_FILE_SIZE_MB`
- **Batch size**: Configurable via `BATCH_SIZE` (recomendado: 100)
- **Rate limiting**: La API maneja automáticamente los límites de OpenAI
- **Caché**: Los embeddings se guardan automáticamente para evitar regeneración

## 🐛 Troubleshooting

### Problemas con Docker

#### Error: "docker-compose command not found"

```bash
# Instalar Docker Compose
# En macOS con Homebrew:
brew install docker-compose

# En Ubuntu/Debian:
sudo apt-get install docker-compose

# Verificar instalación
docker-compose --version
```

#### Error: "Cannot connect to the Docker daemon"

```bash
# Iniciar Docker Desktop (macOS/Windows)
# O iniciar servicio Docker (Linux)
sudo systemctl start docker

# Verificar que Docker esté corriendo
docker ps
```

#### Error: "Port 8000 already in use"

```bash
# Encontrar proceso usando el puerto
lsof -i :8000

# Matar proceso si es necesario
kill -9 <PID>

# O cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usar puerto 8001 en lugar de 8000
```

#### Contenedor no se actualiza con cambios de código

```bash
# Reconstruir imagen sin cache
docker-compose build --no-cache

# Verificar que el volumen esté montado correctamente
docker-compose exec question-answering-api ls -la /app
```

#### Problemas de permisos con volúmenes

```bash
# En Linux, ajustar permisos del directorio data
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data
```

### Problemas generales

#### Error: "OPENAI_API_KEY no está configurada"

```bash
# Verificar que la variable esté configurada
echo $OPENAI_API_KEY

# O en el archivo .env
cat .env | grep OPENAI_API_KEY

# En Docker, verificar dentro del contenedor
docker-compose exec question-answering-api env | grep OPENAI
```

#### Error: "Archivo no encontrado"

- Verificar que la ruta del CSV sea absoluta
- Verificar permisos de lectura del archivo
- Verificar que el archivo no esté vacío
- En Docker: verificar que el archivo esté en el directorio montado

#### Error: "Error al generar embedding"

- Verificar conectividad a internet
- Verificar que la API key de OpenAI sea válida
- Verificar límites de uso de la API de OpenAI
- En Docker: verificar que el contenedor tenga acceso a internet