import os
import sqlite3
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
import unicodedata
import logging
from difflib import SequenceMatcher

# ============================================================
# CONFIGURACIÓN
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL")
IS_PROD = DATABASE_URL is not None
DB_PATH = "data/precios.db"

# Límite absoluto para cualquier medicamento sin rango definido
PRECIO_MAXIMO_ABSOLUTO = 2000.0
# Umbral de similitud para validar nombre_raw vs medicamento
UMBRAL_SIMILITUD = 0.6

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
    # Tabla de precios
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
    
    # Tabla de rangos esperados por medicamento
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rangos_precios (
            medicamento_generico TEXT PRIMARY KEY,
            precio_min REAL,
            precio_max REAL
        )
    ''')
    # Insertar rangos por defecto (ejemplo)
    rangos_default = [
        ('ibuprofeno', 50, 300),
        ('paracetamol', 30, 200),
        ('aspirina', 40, 250),
        # Agrega más según tus datos
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

# ============================================================
# VALIDACIONES (Fixes 1 y 3)
# ============================================================
def validar_coherencia_producto(nombre_raw: str, medicamento_buscado: str) -> bool:
    """Fix 1: Compara nombre_raw con el medicamento normalizado."""
    if not nombre_raw:
        return False
    sim = SequenceMatcher(None, nombre_raw.lower(), medicamento_buscado.lower()).ratio()
    return sim >= UMBRAL_SIMILITUD

def validar_precio(precio: float, medicamento_generico: str, conn) -> bool:
    """Fix 3: Verifica que el precio esté dentro del rango esperado."""
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
        # Sin rango definido: aplicar límite absoluto
        if precio <= PRECIO_MAXIMO_ABSOLUTO:
            return True
        else:
            logging.warning(f"Precio excede límite absoluto para {medicamento_generico}: ${precio}")
            return False

# ============================================================
# GUARDAR PRECIO
# ============================================================
def save_precio(data: Dict[str, Any]):
    required = ['medicamento', 'farmacia', 'precio', 'fuente', 'fecha']
    for field in required:
        if field not in data or data[field] is None:
            raise ValueError(f"Campo '{field}' obligatorio")
    
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
            data.get('url'),
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
            data.get('url'),
            data.get('imagen_url'),
            data['fuente'],
            fecha_str
        ))
    
    conn.commit()
    conn.close()

# ============================================================
# BÚSQUEDA PRINCIPAL (con deduplicación y validaciones)
# ============================================================
def get_precios(medicamento: str, horas: int = 24) -> List[Dict[str, Any]]:
    medicamento_norm = normalizar_texto(medicamento)
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
    
    # Convertir a lista de diccionarios
    resultados = []
    for row in rows:
        if IS_PROD:
            resultados.append(dict(row))
        else:
            resultados.append(dict(row))
    
    # ------------------------------
    # Fix 2: Deduplicación por farmacia (mantener el más reciente)
    # ------------------------------
    mejores_por_farmacia = {}
    for r in resultados:
        farmacia = r['farmacia']
        fecha = r['fecha']
        if farmacia not in mejores_por_farmacia or fecha > mejores_por_farmacia[farmacia]['fecha']:
            mejores_por_farmacia[farmacia] = r
    
    deduplicados = list(mejores_por_farmacia.values())
    
    # ------------------------------
    # Fix 1 y 3: Validar coherencia de nombre y precio
    # ------------------------------
    validados = []
    for r in deduplicados:
        # Fix 1: validar nombre_raw vs medicamento buscado
        nombre_raw = r.get('nombre_raw', '')
        if not validar_coherencia_producto(nombre_raw, medicamento_norm):
            logging.info(f"Descartado por incoherencia de nombre: {nombre_raw} vs {medicamento_norm}")
            continue  # descartar completamente
        
        # Fix 3: validar precio
        precio = r['precio']
        if not validar_precio(precio, medicamento_norm, conn):
            logging.info(f"Descartado por precio anómalo: {precio} para {medicamento_norm}")
            continue
        
        # Si pasa ambas, se agrega
        validados.append(r)
    
    conn.close()
    return validados

# ============================================================
# RESUMEN Y HISTÓRICO (sin cambios, pero usan get_precios)
# ============================================================
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
    
    if IS_PROD:
        return [dict(row) for row in rows]
    else:
        return [dict(row) for row in rows]

def count_precios() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM precios')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ============================================================
# CONTAR POR FUENTE (Fix 4: ya existe, solo aseguramos)
# ============================================================
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