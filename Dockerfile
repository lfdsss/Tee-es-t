FROM node:20-alpine

WORKDIR /app

# Install all dependencies (including dev for build)
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# Copy source
COPY . .

# Build frontend at root path for Express to serve from /
ENV VITE_BASE=/
ENV VITE_OUT_DIR=dist
RUN npx vite build

# Prune dev dependencies after build
RUN npm prune --omit=dev

# Persistent data directory
RUN mkdir -p server/data
VOLUME /app/server/data

EXPOSE 3001

ENV NODE_ENV=production
ENV PORT=3001

CMD ["node", "server/index.js"]
