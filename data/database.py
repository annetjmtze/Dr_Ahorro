import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re  # <-- Nuevo import

DB_PATH = "data/precios.db"

def normalizar(texto: str) -> str:
    """Normaliza texto para búsqueda: minúsculas y espacios simples."""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto.strip().lower())

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            medicamento   TEXT NOT NULL,
            nombre_raw    TEXT,
            farmacia      TEXT NOT NULL,
            ciudad        TEXT,
            precio        REAL NOT NULL,
            precio_promo  REAL,
            vigencia      TEXT,
            url           TEXT,
            fuente        TEXT NOT NULL,
            fecha         TEXT NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_medicamento ON precios(medicamento)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fecha ON precios(fecha)')
    conn.commit()
    conn.close()

def save_precio(data: Dict[str, Any]):
    required = ['medicamento', 'farmacia', 'precio', 'fuente', 'fecha']
    for field in required:
        if field not in data or data[field] is None:
            raise ValueError(f"Campo '{field}' obligatorio")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO precios (
            medicamento, nombre_raw, farmacia, ciudad, precio, precio_promo,
            vigencia, url, fuente, fecha
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['medicamento'],
        data.get('nombre_raw'),
        data['farmacia'],
        data.get('ciudad'),
        data['precio'],
        data.get('precio_promo'),
        data.get('vigencia'),
        data.get('url'),
        data['fuente'],
        data['fecha']
    ))
    conn.commit()
    conn.close()

def get_precios(medicamento: str, horas: int = 24) -> List[Dict[str, Any]]:
    """
    Busca precios para un medicamento. Usa búsqueda parcial e insensible a mayúsculas.
    """
    fecha_limite = (datetime.now() - timedelta(hours=horas)).isoformat()
    termino_normalizado = normalizar(medicamento)
    conn = get_connection()
    cursor = conn.cursor()
    # Usamos LIKE con el término normalizado rodeado de '%'
    cursor.execute('''
        SELECT * FROM precios
        WHERE LOWER(medicamento) LIKE ? AND fecha >= ?
        ORDER BY fecha DESC
    ''', (f'%{termino_normalizado}%', fecha_limite))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_resumen(medicamento: str) -> List[Dict[str, Any]]:
    """
    Devuelve registros de las últimas 24 horas para ese medicamento,
    ordenados de menor a mayor precio.
    """
    fecha_limite = (datetime.now() - timedelta(hours=24)).isoformat()
    termino_normalizado = normalizar(medicamento)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM precios
        WHERE LOWER(medicamento) LIKE ? AND fecha >= ?
        ORDER BY precio ASC
    ''', (f'%{termino_normalizado}%', fecha_limite))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def contar_por_fuente() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT fuente, COUNT(*) as total FROM precios GROUP BY fuente')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]