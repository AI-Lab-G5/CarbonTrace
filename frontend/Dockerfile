# Estágio 1: Build da aplicação React + TypeScript + Vite
FROM node:22-alpine AS builder

WORKDIR /app

# Instalação com cache de camadas
COPY package.json package-lock.json ./
RUN npm ci

# Copia o código-fonte e compila
COPY . .
RUN npm run build

# Estágio 2: Nginx servindo os estáticos e atuando como proxy reverso para o backend
FROM nginx:alpine

# Destino do proxy reverso (configurável pelo compose/ambiente)
ENV BACKEND_URL=http://backend:8000

# Copia os artefatos compilados do estágio anterior
COPY --from=builder /app/dist /usr/share/nginx/html

# Copia a configuração estática e o template com suporte a envsubst
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80 3000

CMD ["nginx", "-g", "daemon off;"]
