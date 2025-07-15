# Dockerfile

# Usa una imagen base oficial de Python
# Se recomienda usar una imagen específica y ligera como python:3.10-slim-buster
FROM python:3.10-slim-buster

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo requirements.txt al directorio de trabajo
# Esto permite que Docker use el cache de la capa si las dependencias no cambian
COPY requirements.txt .

# Instala las dependencias de Python
# --no-cache-dir: No guarda los archivos de caché de pip, reduciendo el tamaño de la imagen
# --upgrade pip: Asegura que pip esté actualizado
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir -p data && chmod -R 777 data

# Copia el resto del código de la aplicación al directorio de trabajo
# El '.' al final indica el directorio actual en el host
COPY . .

# Expone el puerto en el que la aplicación Uvicorn escuchará
# Este es el puerto interno del contenedor, no el puerto del host
EXPOSE 8000

# Define el comando para ejecutar la aplicación Uvicorn
# 0.0.0.0 permite que la aplicación sea accesible desde cualquier interfaz de red dentro del contenedor
# main:app se refiere al objeto 'app' en el archivo 'main.py'
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
