# Nginx development container
FROM nginx:alpine

# Copy development configuration
COPY ./nginx/nginx-dev.conf /etc/nginx/conf.d/default.conf

# Expose ports
EXPOSE 80 443

# Start nginx
CMD ["nginx", "-g", "daemon off;"]