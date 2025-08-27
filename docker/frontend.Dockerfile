FROM node:23.11.0-slim

WORKDIR /app
COPY ./frontend /app

RUN npm install

# Set environment variables with default values
ENV BACKEND_URL=http://backend:8080

# Build the Next.js app
RUN npm run build

# Start the app
CMD ["npm", "start"]
