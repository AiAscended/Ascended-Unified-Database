# ============================================================
# Admin Frontend — Multi-stage Dockerfile
# Stage 1: Build Next.js static export
# Stage 2: Serve with nginx:alpine
# ============================================================

# ── Stage 1: Builder ────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build-time API URL so the static export can embed it
ARG NEXT_PUBLIC_API_URL=http://localhost:8001
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Install dependencies first for better layer caching
COPY package.json ./
RUN npm install --frozen-lockfile

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: Serve ──────────────────────────────────────────
FROM nginx:1.27-alpine AS runner

# Remove default nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy the built static export
COPY --from=builder /app/out /usr/share/nginx/html

# Nginx config: SPA routing with static asset caching
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Run nginx as a non-root user
RUN addgroup --system nginxgroup && adduser --system --ingroup nginxgroup nginxuser \
    && chown -R nginxuser:nginxgroup /usr/share/nginx/html /var/cache/nginx /var/log/nginx \
                                     /etc/nginx/conf.d /etc/nginx/nginx.conf \
    && touch /var/run/nginx.pid && chown nginxuser:nginxgroup /var/run/nginx.pid
USER nginxuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:80/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
