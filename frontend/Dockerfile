FROM nginx:alpine

# Copy a simple index.html
COPY src/index.html /usr/share/nginx/html/

# Expose port 3000 (we'll configure nginx to use this port)
EXPOSE 3000

# Copy nginx configuration to use port 3000
RUN echo 'server { listen 3000; location / { root /usr/share/nginx/html; index index.html; } }' > /etc/nginx/conf.d/default.conf

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
