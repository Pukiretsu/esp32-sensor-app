# BUILD stage
FROM rust:1.86-slim AS builder

WORKDIR /app

# accept the build argument
ARG DATABASE_URL

ENV DATABASE_URL=$DATABASE_URL

COPY . .

RUN cargo build --release && strip target/release/sensor_log_api

# Production

# Etapa 2: Imagen final, mínima y segura
FROM debian:stable-slim

# Crear un usuario no root
RUN useradd -m sensoruser

# Establecer directorio de trabajo
WORKDIR /usr/local/bin

# Copiar el binario desde la build
COPY --from=builder /app/target/release/sensor_log_api .

# Cambiar a usuario seguro
USER sensoruser

# Exponer puerto (ajusta si tu app escucha en otro)
EXPOSE 8080

# Ejecutar el binario
CMD ["./sensor_log_api"]