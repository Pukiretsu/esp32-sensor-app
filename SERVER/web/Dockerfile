FROM nginx:alpine

# Elimina archivos por defecto de Nginx
RUN rm -rf /usr/share/nginx/html/*

# Copia archivos al contenedor
COPY . /usr/share/nginx/html

# Reemplaza la configuración de nginx (opcional)
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]