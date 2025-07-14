# Dockerfile para Next.js con TypeScript
FROM node:18-alpine AS base

# Instalar dependencias solo cuando sea necesario
FROM base AS deps
# Verificar https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine para entender por qué libc6-compat podría ser necesario.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Instalar dependencias basadas en el gestor de paquetes preferido
COPY package.json package-lock.json* ./
RUN npm ci

# Reconstruir el código fuente solo cuando sea necesario
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js recopila datos de telemetría completamente anónimos sobre el uso general.
# Obtén más información aquí: https://nextjs.org/telemetry
# Descomenta la siguiente línea en caso de que quieras deshabilitar la telemetría durante la construcción.
# ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Imagen de producción, copia todos los archivos y ejecuta next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
# Descomenta la siguiente línea en caso de que quieras deshabilitar la telemetría durante el tiempo de ejecución.
# ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Aprovechar automáticamente las trazas de salida para reducir el tamaño de la imagen
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
# establecer hostname a localhost
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]

# Imagen de desarrollo
FROM base AS development
WORKDIR /app

# Instalar dependencias
COPY package.json package-lock.json* ./
RUN npm ci

# Copiar código fuente
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]