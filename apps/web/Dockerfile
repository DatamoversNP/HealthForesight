FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY apps/web/package.json ./

# Install dependencies (use npm install if package-lock.json doesn't exist)
RUN npm install || npm ci

# Copy source
COPY apps/web ./

# Build
RUN npm run build

# Production stage - Using Caddy instead of nginx (no permission issues)
FROM caddy:2.7-alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/caddy

# Copy Caddyfile
COPY apps/web/Caddyfile /etc/caddy/Caddyfile

EXPOSE 80

# Caddy handles permissions automatically, no chown issues
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]

