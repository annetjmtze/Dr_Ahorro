FROM python:3.14-slim

# Instalar Chromium del sistema (para tener dependencias, pero Playwright usará su propia copia)
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# No definir PLAYWRIGHT_BROWSERS_PATH (usar el directorio por defecto)

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar los browsers de Playwright en el directorio por defecto (~/.cache/ms-playwright)
RUN playwright install chromium

COPY . .

CMD ["python", "scheduler.py"]