# Usa una imagen ligera de Python con herramientas de sistema
FROM python:3.14-slim

# Instalar dependencias necesarias para descargar e instalar Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Agregar el repositorio de Google Chrome (método moderno sin apt-key)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instalar Google Chrome estable
RUN apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Variables de entorno para que Playwright use Chrome del sistema
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin
ENV CHROME_PATH=/usr/bin/google-chrome-stable

WORKDIR /app

# Copiar requirements primero (para cachear)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright (para los controladores, pero usaremos Chrome del sistema)
RUN playwright install

# Copiar el resto del código
COPY . .

# Comando por defecto (se sobrescribe en Railway según el servicio)
CMD ["python", "scheduler.py"]