FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY scripts/ ./scripts/

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["python", "-m", "uvicorn", "src.aeropartners.main:app", "--host", "0.0.0.0", "--port", "8000"]
