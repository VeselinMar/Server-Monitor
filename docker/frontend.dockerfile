FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Serve the build with nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Remove default nginx config — replaced by the one injected via compose
RUN rm /etc/nginx/conf.d/default.conf