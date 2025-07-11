# Étape 1 : Build Angular
FROM node:18-alpine AS builder
WORKDIR /app
COPY . .
RUN npm install --force
RUN npm run build --prod

# Étape 2 : Serve Angular via Nginx
FROM nginx:alpine
COPY --from=builder /app/dist/Rhconnect /usr/share/nginx/html


EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
