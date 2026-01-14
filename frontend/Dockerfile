FROM node:18-alpine

WORKDIR /app

# Proxy settings for corporate network (HTTP only - HTTPS proxy commented out)
ENV http_proxy='http://165.225.206.24:10299'
    # https_proxy='http://165.225.206.24:10299' \
    # no_proxy='localhost,127.0.0.1,backend,frontend,nginx'

# Disable SSL verification for Alpine package manager
ENV SSL_VERIFY=false

# Install CA certificates (skip SSL verification for corporate proxy)
RUN apk add --no-cache --allow-untrusted ca-certificates || apk add --no-cache ca-certificates --repository http://dl-cdn.alpinelinux.org/alpine/edge/main --allow-untrusted
COPY ./zscaler.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

# Set NODE_EXTRA_CA_CERTS so Node.js uses the updated CA bundle
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
ENV HTTPS=true 
ENV SSL_CRT_FILE=/cert/certificate.crt 
ENV SSL_KEY_FILE=/cert/certificate.key

# Disable strict SSL for npm (corporate environment)
RUN npm config set strict-ssl false

# Install dependencies
COPY ./frontend/package*.json ./
RUN npm install

# Copy frontend code
COPY ./frontend .

# Accept build argument for API base URL
ARG REACT_APP_API_BASE_URL=https://your-production-server.yourdomain.com:5443
ENV REACT_APP_API_BASE_URL=${REACT_APP_API_BASE_URL}

# Build the production app
RUN npm run build

# Use nginx to serve the built static files
FROM nginx:alpine AS production

# Copy built app from previous stage (Vite builds to 'dist' folder)
COPY --from=0 /app/dist /usr/share/nginx/html

# Copy custom nginx config for serving React SPA
RUN echo 'server { \
    listen 3000; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]