FROM oven/bun:1-slim

WORKDIR /app
COPY ./frontend /app

RUN bun install --frozen-lockfile

# Set environment variables with default values
ENV BACKEND_URL=http://backend:8081

# Build the Next.js app
RUN bun run build

# Start the app
CMD ["bun", "run", "start", "--port", "3001"]
