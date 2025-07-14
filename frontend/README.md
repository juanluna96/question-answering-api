# Question Answering API - Frontend

Frontend desarrollado con Next.js 14, TypeScript y Tailwind CSS para la API de preguntas y respuestas.

## 🚀 Desarrollo Local con Docker

### Prerrequisitos
- Docker
- Docker Compose

### Comandos de Docker

#### Desarrollo (con hot reload)
```bash
# Construir y ejecutar en modo desarrollo
docker-compose up frontend-dev

# Ejecutar en segundo plano
docker-compose up -d frontend-dev

# Ver logs
docker-compose logs -f frontend-dev

# Parar el contenedor
docker-compose down
```

#### Producción
```bash
# Ejecutar en modo producción
docker-compose --profile production up frontend-prod

# Construir imagen de producción
docker-compose --profile production build frontend-prod
```

### URLs de Acceso
- **Desarrollo**: http://localhost:3000
- **Producción**: http://localhost:3001

## 🛠️ Desarrollo Local (sin Docker)

### Instalación
```bash
# Instalar dependencias
npm install

# Ejecutar en modo desarrollo
npm run dev

# Construir para producción
npm run build

# Ejecutar en modo producción
npm start
```

## 📁 Estructura del Proyecto

```
src/
├── app/
│   ├── globals.css      # Estilos globales con Tailwind
│   ├── layout.tsx       # Layout principal
│   └── page.tsx         # Página de inicio
├── components/          # Componentes reutilizables (crear según necesidad)
└── lib/                 # Utilidades y configuraciones (crear según necesidad)
```

## 🐳 Configuración de Docker

### Características del Setup
- **Multi-stage build** para optimización
- **Hot reload** en desarrollo
- **Volúmenes optimizados** para node_modules
- **Network compartida** para integración con backend
- **Profiles** para separar desarrollo y producción

### Variables de Entorno

Docker Compose lee automáticamente las variables del archivo `.env`:

- `NEXT_PUBLIC_API_BACKEND_URL`: URL del backend API (default: http://localhost:8000)
- `NEXT_TELEMETRY_DISABLED`: Deshabilitar telemetría de Next.js (default: 0)
- `NODE_ENV`: Entorno de ejecución

#### Configuración de Variables
```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita las variables según tu configuración
# Ejemplo:
NEXT_PUBLIC_API_BACKEND_URL=http://localhost:8000
NEXT_TELEMETRY_DISABLED=1
```

## 🎨 Tecnologías

- **Next.js 14** - Framework de React
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Framework de CSS
- **Docker** - Containerización
- **ESLint** - Linting de código

## 📝 Scripts Disponibles

- `npm run dev` - Servidor de desarrollo
- `npm run build` - Construir para producción
- `npm run start` - Servidor de producción
- `npm run lint` - Ejecutar ESLint

## 🔧 Configuración Adicional

El proyecto incluye configuraciones optimizadas para:
- TypeScript con paths absolutos (`@/*`)
- Tailwind CSS con gradientes personalizados
- Next.js con App Router
- Docker con multi-stage builds
- PostCSS con Autoprefixer
- Variables de entorno con Docker Compose

### Uso de Variables de Entorno en el Código

```typescript
// Acceder a la URL del backend
const apiUrl = process.env.NEXT_PUBLIC_API_BACKEND_URL;

// Ejemplo de uso en un componente
const fetchData = async () => {
  const response = await fetch(`${apiUrl}/api/questions`);
  return response.json();
};
```

**Nota:** Solo las variables con prefijo `NEXT_PUBLIC_` están disponibles en el cliente. Las demás solo están disponibles en el servidor.