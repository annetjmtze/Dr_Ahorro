import os
import sqlite3
import psycopg
from psycopg.rows import dict_row          # Para obtener filas como diccionarios en PostgreSQL
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import re
import unicodedata

# ============================================================
# CONFIGURACIÓN: detectar entorno automáticamente
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL")
IS_PROD = DATABASE_URL is not None

# Ruta de SQLite (solo para desarrollo local)
DB_PATH = "data/precios.db"

# ============================================================
# CONEXIÓN: PostgreSQL o SQLite según entorno
# ============================================================
def get_connection():
    """Devuelve conexión a PostgreSQL (con row_factory=dict_row) o SQLite."""
    if IS_PROD:
        # PostgreSQL con row_factory para obtener diccionarios directamente
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        # SQLite local (fallback)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

# ============================================================
# INICIALIZAR TABLA (funciona en ambos motores)
# ============================================================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # SQL compatible con PostgreSQL y SQLite
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
    
    # Índices (funcionan en ambos)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_medicamento ON precios(medicamento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fecha ON precios(fecha)')
    
    conn.commit()
    conn.close()

# ============================================================
# GUARDAR PRECIO (compatible con ambos motores)
# ============================================================
def save_precio(data: Dict[str, Any]):
    required = ['medicamento', 'farmacia', 'precio', 'fuente', 'fecha']
    for field in required:
        if field not in data or data[field] is None:
            raise ValueError(f"Campo '{field}' obligatorio")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if IS_PROD:
        # PostgreSQL usa %s como placeholder
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
            data.get('url'),
            data.get('imagen_url'),
            data['fuente'],
            data['fecha']
        ))
    else:
        # SQLite usa ? como placeholder
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
            data.get('url'),
            data.get('imagen_url'),
            data['fuente'],
            data['fecha']
        ))
    
    conn.commit()
    conn.close()

# ============================================================
# NORMALIZACIÓN (sin cambios)
# ============================================================
def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'\s+', ' ', texto)
    return texto

# ============================================================
# BÚSQUEDA PRINCIPAL (últimas 24 horas)
# ============================================================
def get_precios(medicamento: str, horas: int = 24) -> List[Dict[str, Any]]:
    medicamento_norm = normalizar_texto(medicamento)
    fecha_limite = (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if IS_PROD:
        cursor.execute('''
            SELECT * FROM precios
            WHERE LOWER(medicamento) LIKE %s AND fecha >= %s
            ORDER BY fecha DESC
        ''', (f'%{medicamento_norm}%', fecha_limite))
    else:
        cursor.execute('''
            SELECT * FROM precios
            WHERE LOWER(medicamento) LIKE ? AND fecha >= ?
            ORDER BY fecha DESC
        ''', (f'%{medicamento_norm}%', fecha_limite))
    
    rows = cursor.fetchall()
    conn.close()
    
    # En PostgreSQL ya son dict; en SQLite convertimos Row a dict
    if IS_PROD:
        return rows
    else:
        return [dict(row) for row in rows]

def get_resumen(medicamento: str) -> List[Dict[str, Any]]:
    """Alias de get_precios con 24 horas por defecto."""
    return get_precios(medicamento, horas=24)

# ============================================================
# BÚSQUEDA HISTÓRICA (sin límite de tiempo)
# ============================================================
def get_last_precios(medicamento: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Devuelve los últimos `limit` registros del medicamento, sin filtrar por fecha.
    Útil para mostrar datos cuando no hay actualizaciones recientes.
    """
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
    
    if IS_PROD:
        return rows
    else:
        return [dict(row) for row in rows]

# ============================================================
# CONTAR REGISTROS (útil para migración)
# ============================================================
def count_precios() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM precios')
    count = cursor.fetchone()[0]
    conn.close()
    return count