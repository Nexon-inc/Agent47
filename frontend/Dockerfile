# Agent47 Frontend Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install curl for health checks and pnpm
RUN apk add --no-cache curl && \
    npm install -g pnpm

# Copy package files (using pnpm)
COPY package.json pnpm-lock.yaml* ./

# Install dependencies with pnpm
RUN pnpm install --frozen-lockfile || pnpm install --no-frozen-lockfile

# Copy source code
COPY . .

# Build the application
RUN pnpm run build

# Remove dev dependencies to reduce image size
RUN pnpm prune --production

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Start the application
CMD ["pnpm", "start"]
