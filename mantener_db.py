import subprocess
import time
import os
import sys

# Ruta absoluta a tu proyecto (puedes usar la que tiene acento, funciona)
PROJECT_DIR = r'C:\Users\annet\Día5\Webhooks-y-bots-conversacionales'

# Ruta del intérprete de Python dentro del entorno virtual
PYTHON_EXE = os.path.join(PROJECT_DIR, 'venv', 'Scripts', 'python.exe')

# Cambiar al directorio del proyecto
os.chdir(PROJECT_DIR)

while True:
    print(f"\n[{time.ctime()}] Ejecutando scraper para actualizar BD...")
    
    # Ejecuta el scraper usando el Python del venv y forzando el directorio de trabajo
    resultado = subprocess.run(
        [PYTHON_EXE, "-m", "data.scrapers.web_scraper"],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR   # ¡Esto es clave!
    )
    
    print(resultado.stdout)
    if resultado.stderr:
        print("ERROR:", resultado.stderr)
    
    print(f"[{time.ctime()}] Scraper terminado. Esperando 4 horas...")
    time.sleep(14400)   # 4 horas