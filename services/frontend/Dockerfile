# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
# Setting arg so we can pass API URL during build if needed
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Serve stage
FROM nginx:alpine

# Copy built assets to Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Replace default config with our SPA optimized config
COPY nginx-frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
