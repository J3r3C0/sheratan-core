FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy TypeScript config and source code
COPY tsconfig.json ./
COPY src/ ./src/
COPY config/ ./config/

# Build TypeScript
RUN npm run build

# Expose HTTP API port
EXPOSE 3000

# Set environment variables for Docker
ENV BROWSER_URL=http://host.docker.internal:9222
ENV WEB_INTERFACE_URL=https://chatgpt.com
ENV PORT=3000

# Start the worker
CMD ["npm", "start"]
