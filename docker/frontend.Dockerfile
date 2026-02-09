FROM oven/bun:1-slim

WORKDIR /app
COPY ./frontend /app

RUN bun install --frozen-lockfile

# Set environment variables with default values
ENV BACKEND_URL=http://sqlmate-backend:8081

# NEXT_PUBLIC_* vars must be available at build time for Next.js to inline them
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

# Build the Next.js app
RUN bun run build

# Start the app
CMD ["bun", "run", "start", "--port", "3001"]
