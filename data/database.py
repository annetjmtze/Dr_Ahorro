import os
import sqlite3
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import re
import unicodedata
import logging
from difflib import SequenceMatcher
from urllib.parse import urlparse  # 👈 NUEVA IMPORTACIÓN

# ============================================================
# CONFIGURACIÓN
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL")
IS_PROD = DATABASE_URL is not None
DB_PATH = "data/precios.db"

PRECIO_MAXIMO_ABSOLUTO = 2000.0
UMBRAL_SIMILITUD = 0.3

logging.basicConfig(level=logging.INFO)

def get_connection():
    if IS_PROD:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precios (
            id SERIAL PRIMARY KEY,
            medicamento TEXT NOT NULL,
            nombre_raw TEXT,
            farmacia TEXT NOT NULL,
            ciudad TEXT,
            precio REAL NOT NULL,
            precio_promo REAL,
            vigencia TEXT,
            url TEXT,
            imagen_url TEXT,
            fuente TEXT NOT NULL,
            fecha TEXT NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_medicamento ON precios(medicamento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fecha ON precios(fecha)')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rangos_precios (
            medicamento_generico TEXT PRIMARY KEY,
            precio_min REAL,
            precio_max REAL
        )
    ''')
    rangos_default = [
        ('ibuprofeno', 5, 1000),
        ('paracetamol', 5, 800),
        ('aspirina', 5, 800),
    ]
    if IS_PROD:
        cursor.executemany(
            'INSERT INTO rangos_precios (medicamento_generico, precio_min, precio_max) VALUES (%s, %s, %s) '
            'ON CONFLICT (medicamento_generico) DO NOTHING',
            rangos_default
        )
    else:
        cursor.executemany(
            'INSERT OR IGNORE INTO rangos_precios (medicamento_generico, precio_min, precio_max) VALUES (?, ?, ?)',
            rangos_default
        )
    conn.commit()
    conn.close()

def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def normalizar_farmacia(nombre: str) -> str:
    """
    Normaliza el nombre de la farmacia para deduplicación (case-insensitive).
    Extrae el nombre entre paréntesis si existe, elimina palabras comunes y convierte a minúsculas.
    """
    if not nombre:
        return ""
    # Extraer lo que está entre paréntesis (ej: "Rappi (Farmacias Guadalajara)")
    match = re.search(r'\(([^)]+)\)', nombre)
    if match:
        nombre = match.group(1)
    # Limpiar y normalizar
    nombre = nombre.lower().strip()
    # Eliminar palabras comunes para agrupar mejor
    nombre = re.sub(r'\bfarmacias?\b', '', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    return nombre

def validar_coherencia_producto(nombre_raw: str, medicamento_buscado: str) -> bool:
    if not nombre_raw:
        return False
    nombre_raw_lower = nombre_raw.lower()
    medicamento_buscado_lower = medicamento_buscado.lower()
    if medicamento_buscado_lower in nombre_raw_lower:
        return True
    sim = SequenceMatcher(None, nombre_raw_lower, medicamento_buscado_lower).ratio()
    return sim >= UMBRAL_SIMILITUD

def validar_precio(precio: float, medicamento_generico: str, conn) -> bool:
    if precio <= 0:
        return False
    cursor = conn.cursor()
    if IS_PROD:
        cursor.execute(
            "SELECT precio_min, precio_max FROM rangos_precios WHERE medicamento_generico = %s",
            (medicamento_generico,)
        )
    else:
        cursor.execute(
            "SELECT precio_min, precio_max FROM rangos_precios WHERE medicamento_generico = ?",
            (medicamento_generico,)
        )
    row = cursor.fetchone()
    if row:
        if IS_PROD:
            precio_min = row['precio_min']
            precio_max = row['precio_max']
        else:
            precio_min = row[0]
            precio_max = row[1]
        limite_inf = precio_min * 0.1
        limite_sup = precio_max * 10
        if limite_inf <= precio <= limite_sup:
            return True
        else:
            logging.warning(f"Precio fuera de rango para {medicamento_generico}: ${precio} (rango esperado: {limite_inf} - {limite_sup})")
            return False
    else:
        if precio <= PRECIO_MAXIMO_ABSOLUTO:
            return True
        else:
            logging.warning(f"Precio excede límite absoluto para {medicamento_generico}: ${precio}")
            return False

# ============================================================
# VALIDACIÓN DE URL (NUEVO)
# ============================================================
def es_url_valida(url: str) -> bool:
    """Verifica si la URL es válida (tiene esquema http/https y netloc)."""
    if not url:
        return False
    try:
        r = urlparse(url)
        return r.scheme in ('http', 'https') and bool(r.netloc)
    except:
        return False

def save_precio(data: Dict[str, Any]):
    required = ['medicamento', 'farmacia', 'precio', 'fuente', 'fecha']
    for field in required:
        if field not in data or data[field] is None:
            raise ValueError(f"Campo '{field}' obligatorio")
    
    # ---- VALIDAR URL (NUEVO) ----
    url = data.get('url')
    if url and not es_url_valida(url):
        logging.warning(f"URL inválida detectada: {url} — se guardará como NULL")
        data['url'] = None  # o '' según prefieras
    
    fecha_str = data['fecha']
    if not IS_PROD:
        fecha_str = fecha_str.replace('Z', '').replace('+00:00', '')
        if '.' in fecha_str:
            fecha_str = fecha_str.split('.')[0]
        fecha_str = fecha_str.replace('T', ' ')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if IS_PROD:
        cursor.execute('''
            INSERT INTO precios (
                medicamento, nombre_raw, farmacia, ciudad, precio, precio_promo,
                vigencia, url, imagen_url, fuente, fecha
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data['medicamento'],
            data.get('nombre_raw'),
            data['farmacia'],
            data.get('ciudad'),
            data['precio'],
            data.get('precio_promo'),
            data.get('vigencia'),
            data.get('url'),  # Ya validado
            data.get('imagen_url'),
            data['fuente'],
            fecha_str
        ))
    else:
        cursor.execute('''
            INSERT INTO precios (
                medicamento, nombre_raw, farmacia, ciudad, precio, precio_promo,
                vigencia, url, imagen_url, fuente, fecha
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['medicamento'],
            data.get('nombre_raw'),
            data['farmacia'],
            data.get('ciudad'),
            data['precio'],
            data.get('precio_promo'),
            data.get('vigencia'),
            data.get('url'),  # Ya validado
            data.get('imagen_url'),
            data['fuente'],
            fecha_str
        ))
    
    conn.commit()
    conn.close()

def get_precios(medicamento: str, horas: int = 24) -> List[Dict[str, Any]]:
    medicamento_norm = normalizar_texto(medicamento)
    logging.info(f"🔍 Buscando: {medicamento_norm}")
    conn = get_connection()
    cursor = conn.cursor()
    
    if IS_PROD:
        fecha_limite = (datetime.utcnow() - timedelta(hours=horas)).isoformat()
        cursor.execute('''
            SELECT * FROM precios
            WHERE LOWER(medicamento) LIKE %s AND fecha >= %s
            ORDER BY fecha DESC
        ''', (f'%{medicamento_norm}%', fecha_limite))
    else:
        fecha_limite = (datetime.utcnow() - timedelta(hours=horas)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            SELECT * FROM precios
            WHERE LOWER(medicamento) LIKE ? AND fecha >= ?
            ORDER BY fecha DESC
        ''', (f'%{medicamento_norm}%', fecha_limite))
    
    rows = cursor.fetchall()
    resultados = [dict(row) for row in rows]
    logging.info(f"📦 Registros obtenidos de BD: {len(resultados)}")
    
    filtrados_coherencia = []
    for r in resultados:
        nombre_raw = r.get('nombre_raw', '')
        if validar_coherencia_producto(nombre_raw, medicamento_norm):
            filtrados_coherencia.append(r)
        else:
            logging.info(f"  ❌ Descartado por coherencia: {nombre_raw[:40]}... | vs {medicamento_norm}")
    
    filtrados_precio = []
    for r in filtrados_coherencia:
        if validar_precio(r['precio'], medicamento_norm, conn):
            filtrados_precio.append(r)
        else:
            logging.info(f"  ❌ Descartado por precio: ${r['precio']} - {r.get('nombre_raw', '')[:30]}")
    
    mejores = {}
    for r in filtrados_precio:
        farmacia_norm = normalizar_farmacia(r['farmacia'])
        if farmacia_norm not in mejores or r['fecha'] > mejores[farmacia_norm]['fecha']:
            mejores[farmacia_norm] = r
    
    conn.close()
    final = list(mejores.values())
    logging.info(f"✅ Resultados finales después de deduplicar: {len(final)}")
    return final

def get_resumen(medicamento: str) -> List[Dict[str, Any]]:
    return get_precios(medicamento, horas=24)

def get_last_precios(medicamento: str, limit: int = 5) -> List[Dict[str, Any]]:
    medicamento_norm = normalizar_texto(medicamento)
    conn = get_connection()
    cursor = conn.cursor()
    
    if IS_PROD:
        cursor.execute('''
            SELECT * FROM precios
            WHERE LOWER(medicamento) LIKE %s
            ORDER BY fecha DESC
            LIMIT %s
        ''', (f'%{medicamento_norm}%', limit))
    else:
        cursor.execute('''
            SELECT * FROM precios
            WHERE LOWER(medicamento) LIKE ?
            ORDER BY fecha DESC
            LIMIT ?
        ''', (f'%{medicamento_norm}%', limit))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def count_precios() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM precios')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def contar_por_fuente():
    conn = get_connection()
    cursor = conn.cursor()
    if IS_PROD:
        cursor.execute("SELECT fuente, COUNT(*) FROM precios GROUP BY fuente")
    else:
        cursor.execute("SELECT fuente, COUNT(*) FROM precios GROUP BY fuente")
    rows = cursor.fetchall()
    conn.close()
    resultado = {}
    for row in rows:
        if IS_PROD:
            fuente = row['fuente']
            count = row['count']
        else:
            fuente = row[0]
            count = row[1]
        resultado[fuente] = count
    return resultado