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

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

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
```

### 3. Crear directorios necesarios

```bash
mkdir -p data/cache
mkdir -p data/uploads
```

## 🏃‍♂️ Ejecución

### Desarrollo

```bash
# Desde el directorio backend/
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

La API estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔗 Endpoints Principales

### 1. Cargar Embeddings

```http
POST /embeddings/load
Content-Type: application/json

{
  "csv_file_path": "/path/to/your/file.csv",
  "cache_file_path": "/path/to/cache.pkl",
  "force_regenerate": false
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Embeddings procesados exitosamente desde /path/to/file.csv",
  "embeddings_count": 150,
  "cache_used": true,
  "model_info": {
    "model": "text-embedding-3-small",
    "provider": "OpenAI",
    "dimensions": 1536
  }
}
```

### 2. Estado del Caché

```http
GET /embeddings/cache/status?cache_file_path=/path/to/cache.pkl
```

**Respuesta:**
```json
{
  "exists": true,
  "file_path": "/path/to/cache.pkl",
  "size_bytes": 2048576,
  "size_mb": 2.05,
  "embeddings_count": 150,
  "last_modified": 1703123456.789
}
```

### 3. Health Check

```http
GET /health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "question-answering-api",
  "version": "1.0.0",
  "config": {
    "openai_configured": true,
    "model": "text-embedding-3-small",
    "cache_path": "./data/cache/embeddings.pkl"
  }
}
```

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

## 🧪 Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest
```

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

### Error: "OPENAI_API_KEY no está configurada"

```bash
# Verificar que la variable esté configurada
echo $OPENAI_API_KEY

# O en el archivo .env
cat .env | grep OPENAI_API_KEY
```

### Error: "Archivo no encontrado"

- Verificar que la ruta del CSV sea absoluta
- Verificar permisos de lectura del archivo
- Verificar que el archivo no esté vacío

### Error: "Error al generar embedding"

- Verificar conectividad a internet
- Verificar que la API key de OpenAI sea válida
- Verificar límites de uso de la API de OpenAI

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.