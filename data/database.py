import os
import sys
import sqlite3
import psycopg
from psycopg.rows import dict_row
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import re
import unicodedata
import logging
from difflib import SequenceMatcher
from urllib.parse import urlparse

# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL")
IS_PROD = DATABASE_URL is not None
DB_PATH = "data/precios.db"

PRECIO_MAXIMO_ABSOLUTO = 2000.0
UMBRAL_SIMILITUD = 0.3

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

    # --- Tabla de precios (existente) ---
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

    # --- Tabla de rangos (existente) ---
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
        ('omeprazol', 5, 600),
        ('naproxeno', 5, 800),
        ('metformina', 5, 500),
        ('losartan', 5, 500),
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

    # --- Tabla de usuarios (existente) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id              SERIAL PRIMARY KEY,
            whatsapp_number TEXT UNIQUE NOT NULL,
            colonia         TEXT,
            codigo_postal   TEXT,
            ciudad          TEXT DEFAULT 'Ciudad de México',
            latitud         REAL,
            longitud        REAL,
            zona_verificada BOOLEAN DEFAULT FALSE,
            created_at      TEXT NOT NULL,
            ultima_busqueda TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp ON usuarios(whatsapp_number)')

    # ------------------------------------------------------------
    # TABLA analisis_busquedas (con todas las columnas)
    # ------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analisis_busquedas (
            id                  SERIAL PRIMARY KEY,
            usuario             TEXT NOT NULL,
            medicamento         TEXT NOT NULL,
            urgente             BOOLEAN DEFAULT FALSE,
            opcion_ganadora     TEXT,
            ahorro_calculado    REAL,
            zona                TEXT,
            opcion_recomendada  TEXT,
            precio_recomendado  REAL,
            precio_rappi        REAL,
            precio_fisica       REAL,
            fecha               TEXT NOT NULL
        )
    ''')

    # ------------------------------------------------------------
    # MIGRACIONES (antes de crear índices)
    # ------------------------------------------------------------
    if IS_PROD:
        # PostgreSQL: renombrar timestamp a fecha si existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='analisis_busquedas' AND column_name='timestamp'
        """)
        if cursor.fetchone():
            cursor.execute("ALTER TABLE analisis_busquedas RENAME COLUMN timestamp TO fecha")
            logger.info("✅ Columna 'timestamp' renombrada a 'fecha' (PostgreSQL)")

        # Agregar columnas nuevas si no existen
        for col, tipo in [
            ("zona", "TEXT"),
            ("opcion_recomendada", "TEXT"),
            ("precio_recomendado", "REAL"),
            ("precio_rappi", "REAL"),
            ("precio_fisica", "REAL"),
            ("ahorro_calculado", "REAL"),
        ]:
            cursor.execute(f"ALTER TABLE analisis_busquedas ADD COLUMN IF NOT EXISTS {col} {tipo}")
    else:
        # SQLite: renombrar timestamp a fecha si existe
        try:
            cursor.execute("ALTER TABLE analisis_busquedas RENAME COLUMN timestamp TO fecha")
            logger.info("✅ Columna 'timestamp' renombrada a 'fecha' (SQLite)")
        except Exception as e:
            if "no such column" not in str(e).lower():
                logger.warning(f"Error al renombrar columna: {e}")

        # Agregar columnas nuevas (si ya existen, ignorar error)
        for col, tipo in [
            ("zona", "TEXT"),
            ("opcion_recomendada", "TEXT"),
            ("precio_recomendado", "REAL"),
            ("precio_rappi", "REAL"),
            ("precio_fisica", "REAL"),
            ("ahorro_calculado", "REAL"),
        ]:
            try:
                cursor.execute(f"ALTER TABLE analisis_busquedas ADD COLUMN {col} {tipo}")
            except Exception:
                pass  # Columna ya existe

    # ------------------------------------------------------------
    # ÍNDICES (después de las migraciones)
    # ------------------------------------------------------------
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analisis_usuario ON analisis_busquedas(usuario)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analisis_fecha ON analisis_busquedas(fecha)')

    conn.commit()
    conn.close()
    logger.info("📦 Base de datos inicializada correctamente")


# ============================================================
# FUNCIONES DE NORMALIZACIÓN
# ============================================================
def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def normalizar_farmacia(nombre: str) -> str:
    if not nombre:
        return ""
    match = re.search(r'\(([^)]+)\)', nombre)
    if match:
        nombre = match.group(1)
    nombre = nombre.lower().strip()
    nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('ASCII')
    nombre = re.sub(r'\bfarmacia(s)?\b', '', nombre)
    nombre = re.sub(r'\b(de|la|el|y|del)\b', '', nombre)
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
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
            logger.warning(f"Precio fuera de rango para {medicamento_generico}: ${precio} (rango esperado: {limite_inf} - {limite_sup})")
            return False
    else:
        if precio <= PRECIO_MAXIMO_ABSOLUTO:
            return True
        else:
            logger.warning(f"Precio excede límite absoluto para {medicamento_generico}: ${precio}")
            return False

def es_url_valida(url: str) -> bool:
    if not url:
        return False
    try:
        r = urlparse(url)
        return r.scheme in ('http', 'https') and bool(r.netloc)
    except:
        return False


# ============================================================
# FUNCIONES DE PRECIOS
# ============================================================
def save_precio(data: Dict[str, Any]):
    required = ['medicamento', 'farmacia', 'precio', 'fuente', 'fecha']
    for field in required:
        if field not in data or data[field] is None:
            raise ValueError(f"Campo '{field}' obligatorio")
    
    url = data.get('url')
    if url and not es_url_valida(url):
        logger.warning(f"URL inválida detectada: {url} — se guardará como NULL")
        data['url'] = None
    
    fecha_str = data['fecha']
    if not IS_PROD:
        fecha_str = fecha_str.replace('Z', '').replace('+00:00', '')
        if '.' in fecha_str:
            fecha_str = fecha_str.split('.')[0]
        fecha_str = fecha_str.replace('T', ' ')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    fecha_dia = fecha_str[:10]
    if IS_PROD:
        cursor.execute(
            "SELECT 1 FROM precios WHERE medicamento = %s AND farmacia = %s AND DATE(fecha) = %s LIMIT 1",
            (data['medicamento'], data['farmacia'], fecha_dia)
        )
    else:
        cursor.execute(
            "SELECT 1 FROM precios WHERE medicamento = ? AND farmacia = ? AND DATE(fecha) = ? LIMIT 1",
            (data['medicamento'], data['farmacia'], fecha_dia)
        )
    if cursor.fetchone():
        logger.info(f"⚠️ Registro duplicado para {data['medicamento']} en {data['farmacia']} (fecha {fecha_dia}), omitiendo inserción.")
        conn.close()
        return
    
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


def get_precios(medicamento: str, horas: int = 24) -> List[Dict[str, Any]]:
    medicamento_norm = normalizar_texto(medicamento)
    logger.info(f"🔍 Buscando: {medicamento_norm}")
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
    logger.info(f"📦 Registros obtenidos de BD: {len(resultados)}")
    
    filtrados_coherencia = []
    for r in resultados:
        nombre_raw = r.get('nombre_raw', '')
        if validar_coherencia_producto(nombre_raw, medicamento_norm):
            filtrados_coherencia.append(r)
        else:
            logger.info(f"  ❌ Descartado por coherencia: {nombre_raw[:40]}... | vs {medicamento_norm}")
    
    filtrados_precio = []
    for r in filtrados_coherencia:
        if validar_precio(r['precio'], medicamento_norm, conn):
            filtrados_precio.append(r)
        else:
            logger.info(f"  ❌ Descartado por precio: ${r['precio']} - {r.get('nombre_raw', '')[:30]}")
    
    mejores = {}
    for r in filtrados_precio:
        farmacia_norm = normalizar_farmacia(r['farmacia'])
        if farmacia_norm not in mejores or r['fecha'] > mejores[farmacia_norm]['fecha']:
            mejores[farmacia_norm] = r
    
    conn.close()
    final = list(mejores.values())
    logger.info(f"✅ Resultados finales después de deduplicar: {len(final)}")
    return final


def get_resumen(medicamento: str) -> List[Dict[str, Any]]:
    """Alias de get_precios con horizonte de 24 horas."""
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
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return 0
    if IS_PROD:
        return row.get('count', 0) or 0
    else:
        return row[0] or 0


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


# ============================================================
# FUNCIONES DE USUARIO
# ============================================================
def get_usuario(whatsapp_number: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if IS_PROD:
        cursor.execute(
            "SELECT * FROM usuarios WHERE whatsapp_number = %s",
            (whatsapp_number,)
        )
    else:
        cursor.execute(
            "SELECT * FROM usuarios WHERE whatsapp_number = ?",
            (whatsapp_number,)
        )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def _save_usuario(whatsapp_number: str, data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    
    if IS_PROD:
        cursor.execute(
            """
            INSERT INTO usuarios (
                whatsapp_number, colonia, codigo_postal, ciudad, latitud, longitud,
                zona_verificada, created_at, ultima_busqueda
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (whatsapp_number) DO UPDATE SET
                colonia = EXCLUDED.colonia,
                codigo_postal = EXCLUDED.codigo_postal,
                ciudad = EXCLUDED.ciudad,
                latitud = EXCLUDED.latitud,
                longitud = EXCLUDED.longitud,
                zona_verificada = EXCLUDED.zona_verificada,
                ultima_busqueda = EXCLUDED.ultima_busqueda
            """,
            (
                whatsapp_number,
                data.get('colonia'),
                data.get('codigo_postal'),
                data.get('ciudad'),
                data.get('latitud'),
                data.get('longitud'),
                data.get('zona_verificada', False),
                data.get('created_at', datetime.now(timezone.utc).isoformat()),
                data.get('ultima_busqueda', datetime.now(timezone.utc).isoformat())
            )
        )
    else:
        cursor.execute(
            """
            INSERT OR REPLACE INTO usuarios (
                whatsapp_number, colonia, codigo_postal, ciudad, latitud, longitud,
                zona_verificada, created_at, ultima_busqueda
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                whatsapp_number,
                data.get('colonia'),
                data.get('codigo_postal'),
                data.get('ciudad', 'Ciudad de México'),
                data.get('latitud'),
                data.get('longitud'),
                data.get('zona_verificada', False),
                data.get('created_at', datetime.now(timezone.utc).isoformat()),
                data.get('ultima_busqueda', datetime.now(timezone.utc).isoformat())
            )
        )
    conn.commit()
    conn.close()


def save_zona_texto(whatsapp_number: str, colonia: str, cp: Optional[str] = None, ciudad: Optional[str] = None):
    data = {
        'colonia': colonia.strip() if colonia else None,
        'codigo_postal': cp.strip() if cp else None,
        'ciudad': ciudad.strip() if ciudad else None,
        'zona_verificada': True,
        'ultima_busqueda': datetime.now(timezone.utc).isoformat()
    }
    _save_usuario(whatsapp_number, data)
    logger.info(f"✅ Zona guardada para {whatsapp_number}: colonia='{colonia}', CP='{cp}', ciudad='{ciudad}'")


def save_zona_gps(whatsapp_number: str, lat: float, lon: float):
    data = {
        'latitud': lat,
        'longitud': lon,
        'zona_verificada': True,
        'ultima_busqueda': datetime.now(timezone.utc).isoformat()
    }
    _save_usuario(whatsapp_number, data)
    logger.info(f"✅ GPS guardado para {whatsapp_number}: lat={lat}, lon={lon}")


def actualizar_zona(
    whatsapp_number: str,
    colonia: Optional[str] = None,
    cp: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None
):
    data = {}
    if colonia is not None:
        data['colonia'] = colonia.strip()
    if cp is not None:
        data['codigo_postal'] = cp.strip()
    if lat is not None:
        data['latitud'] = lat
    if lon is not None:
        data['longitud'] = lon
    if not data:
        logger.warning("No se proporcionaron datos para actualizar zona")
        return
    data['zona_verificada'] = True
    data['ultima_busqueda'] = datetime.now(timezone.utc).isoformat()
    _save_usuario(whatsapp_number, data)
    logger.info(f"🔄 Zona actualizada para {whatsapp_number}: {data}")


def clear_zona(whatsapp_number: str):
    data = {
        'colonia': None,
        'codigo_postal': None,
        'latitud': None,
        'longitud': None,
        'zona_verificada': False,
        'ultima_busqueda': datetime.now(timezone.utc).isoformat()
    }
    _save_usuario(whatsapp_number, data)
    logger.info(f"🧹 Zona limpiada para {whatsapp_number}")


# ============================================================
# FUNCIÓN GUARDAR ANÁLISIS (ACTUALIZADA)
# ============================================================
def guardar_analisis(
    usuario: str,
    medicamento: str,
    urgente: bool,
    opcion_ganadora: Optional[str],
    ahorro_calculado: float,
    zona: Optional[str] = None,
    opcion_recomendada: Optional[str] = None,
    precio_recomendado: Optional[float] = None,
    precio_rappi: Optional[float] = None,
    precio_fisica: Optional[float] = None,
    fecha: Optional[datetime] = None
):
    if fecha is None:
        fecha = datetime.now(timezone.utc)
    fecha_str = fecha.isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        if IS_PROD:
            cursor.execute(
                """
                INSERT INTO analisis_busquedas
                (usuario, medicamento, urgente, opcion_ganadora, ahorro_calculado,
                 zona, opcion_recomendada, precio_recomendado, precio_rappi, precio_fisica, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (usuario, medicamento, urgente, opcion_ganadora, ahorro_calculado,
                 zona, opcion_recomendada, precio_recomendado, precio_rappi, precio_fisica, fecha_str)
            )
        else:
            cursor.execute(
                """
                INSERT INTO analisis_busquedas
                (usuario, medicamento, urgente, opcion_ganadora, ahorro_calculado,
                 zona, opcion_recomendada, precio_recomendado, precio_rappi, precio_fisica, fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (usuario, medicamento, urgente, opcion_ganadora, ahorro_calculado,
                 zona, opcion_recomendada, precio_recomendado, precio_rappi, precio_fisica, fecha_str)
            )
        conn.commit()
        logger.info(f"✅ Análisis guardado para {usuario}: {medicamento}, urgente={urgente}")
    except Exception as e:
        logger.error(f"❌ Error guardando análisis en BD: {e}")
    finally:
        conn.close()