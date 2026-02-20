# Stage 1: Build
FROM node:18-alpine as build-stage

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Stage 2: Serve
FROM nginx:stable-alpine as production-stage

# Copy Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from build-stage
# Quasar builds to /dist/spa by default for SPA mode
COPY --from=build-stage /app/dist/spa /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
