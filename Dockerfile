# Usamos una imagen slim pero con herramientas necesarias
FROM python:3.11-slim

# ── Variables de entorno ──
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/usr/bin \
    CHROME_PATH=/usr/bin/google-chrome-stable

# ── Instalar dependencias del sistema ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome y dependencias
    wget \
    gnupg \
    curl \
    unzip \
    # Tesseract OCR y dependencias
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    libleptonica-dev \
    # Bibliotecas para Pillow (procesamiento de imágenes)
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    libfreetype-dev \
    # Otras utilidades
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Instalar Google Chrome ──
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ── Directorio de trabajo ──
WORKDIR /app

# ── Copiar requirements e instalar dependencias Python ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Instalar Playwright y sus navegadores (solo Chromium) ──
# Pero como usamos Chrome del sistema, solo instalamos los controladores
RUN playwright install chromium

# ── Copiar el código fuente ──
COPY . .

# ── Comando por defecto (puedes sobrescribirlo en Railway) ──
CMD ["python", "scheduler.py"]