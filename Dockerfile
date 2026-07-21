# Usa una imagen ligera de Python con herramientas de sistema
FROM python:3.14-slim

# Instala Chromium y sus dependencias (necesario para Playwright)
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Variables de entorno para que Playwright use Chromium del sistema
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin
ENV CHROME_PATH=/usr/bin/chromium

# Directorio de trabajo
WORKDIR /app

# Copiar requirements primero (para cachear capas)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando por defecto (se puede sobrescribir en Railway)
CMD ["python", "scheduler.py"]