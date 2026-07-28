import os
import asyncio
import random
import hashlib
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import logging

from playwright.async_api import async_playwright
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN DE R2 DESDE ENTORNO
# ============================================================
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT_URL")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "dr-ahorro-screenshots")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

CACHE_EXPIRATION_HOURS = 6

if R2_ACCESS_KEY:
    logger.info(f"🔑 R2_ACCESS_KEY configurada (primeros 4: {R2_ACCESS_KEY[:4]}...)")
else:
    logger.warning("⚠️ R2_ACCESS_KEY no está definida")

if R2_PUBLIC_URL:
    logger.info(f"🌐 R2_PUBLIC_URL: {R2_PUBLIC_URL}")
else:
    logger.warning("⚠️ R2_PUBLIC_URL no está definida")

# ============================================================
# CLIENTE R2
# ============================================================
def get_r2_client():
    if not R2_ACCESS_KEY:
        raise ValueError("❌ R2_ACCESS_KEY no está configurada")
    if not R2_SECRET_KEY:
        raise ValueError("❌ R2_SECRET_KEY no está configurada")
    if not R2_ENDPOINT:
        raise ValueError("❌ R2_ENDPOINT no está configurado")
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )

# ============================================================
# GENERACIÓN DE CLAVE PARA CACHÉ
# ============================================================
def generar_key_para_busqueda(zona: str = "", ciudad: str = "", lat: float = None, lon: float = None) -> str:
    if lat is not None and lon is not None:
        base = f"gps_{lat:.6f}_{lon:.6f}"
    elif zona and ciudad:
        base = f"{zona}_{ciudad}".lower().strip()
    elif zona:
        base = f"{zona}".lower().strip()
    else:
        base = "unknown"
    base_limpia = base.replace(' ', '_').replace(',', '').replace('.', '')
    hash_obj = hashlib.md5(base.encode('utf-8')).hexdigest()[:8]
    return f"mapas/{base_limpia}_{hash_obj}.png"

# ============================================================
# FUNCIONES DE CACHÉ
# ============================================================
def obtener_imagen_cacheada(zona: str = "", ciudad: str = "", lat: float = None, lon: float = None) -> Optional[Tuple[str, datetime]]:
    try:
        client = get_r2_client()
    except ValueError as e:
        logger.error(f"❌ Error al obtener cliente R2: {e}")
        return None

    key = generar_key_para_busqueda(zona, ciudad, lat, lon)
    try:
        head = client.head_object(Bucket=R2_BUCKET, Key=key)
        last_modified = head['LastModified']
        ahora = datetime.now(timezone.utc)
        if ahora - last_modified < timedelta(hours=CACHE_EXPIRATION_HOURS):
            url_publica = f"{R2_PUBLIC_URL}/{key}"
            return (url_publica, last_modified)
        else:
            logger.info(f"🗑️ Caché expirado para {key}")
            return None
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info(f"📭 No hay caché para {key}")
        else:
            logger.error(f"❌ Error al verificar caché: {e}")
        return None

def guardar_imagen_en_r2(zona: str = "", ciudad: str = "", lat: float = None, lon: float = None, imagen_bytes: bytes = None) -> str:
    try:
        client = get_r2_client()
    except ValueError as e:
        logger.error(f"❌ Error al obtener cliente R2: {e}")
        raise

    key = generar_key_para_busqueda(zona, ciudad, lat, lon)
    try:
        client.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=imagen_bytes,
            ContentType='image/png',
            ACL='public-read'
        )
        url_publica = f"{R2_PUBLIC_URL}/{key}"
        logger.info(f"✅ Imagen guardada en R2: {url_publica}")
        return url_publica
    except Exception as e:
        logger.error(f"❌ Error al guardar imagen: {e}")
        raise

# ============================================================
# CAPTURA DE MAPA CON PLAYWRIGHT
# ============================================================
async def capturar_mapa_farmacias(
    zona: str = None,
    ciudad: str = None,
    lat: float = None,
    lon: float = None
) -> Optional[bytes]:
    try:
        # Construir la URL según el tipo de búsqueda
        if lat is not None and lon is not None:
            # GPS: usar solo coordenadas + México
            query = f"{lat},{lon} México"
        elif zona and ciudad:
            # Colonia + ciudad
            query = f"farmacias cerca de {zona}, {ciudad} México"
        elif zona:
            # Solo zona (puede ser colonia o CP) + México
            query = f"farmacias cerca de {zona} México"
        else:
            logger.error("❌ No hay suficiente información para generar el mapa")
            return None

        # Codificar la URL
        url = f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"
        logger.info(f"🗺️ Abriendo Google Maps: {url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 800, "height": 600},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            try:
                await page.wait_for_selector('[role="main"]', timeout=15000)
                await asyncio.sleep(random.uniform(3, 5))
            except Exception as e:
                logger.warning(f"⚠️ No se pudo detectar el mapa correctamente: {e}")

            screenshot = await page.screenshot(
                clip={"x": 350, "y": 0, "width": 450, "height": 600},
                type='png'
            )
            await browser.close()
            return screenshot
    except Exception as e:
        logger.error(f"❌ Error en capturar_mapa_farmacias: {e}")
        return None

# ============================================================
# FUNCIÓN PRINCIPAL ASÍNCRONA
# ============================================================
async def obtener_mapa_para_zona(
    zona: str = None,
    ciudad: str = None,
    lat: float = None,
    lon: float = None
) -> Optional[str]:
    cached = obtener_imagen_cacheada(zona, ciudad, lat, lon)
    if cached:
        url, fecha = cached
        logger.info(f"♻️ Usando caché para {zona} {ciudad} {lat} {lon} (generado: {fecha})")
        return url

    logger.info(f"🆕 Generando nuevo mapa para {zona} {ciudad} {lat} {lon}")
    imagen_bytes = await capturar_mapa_farmacias(zona, ciudad, lat, lon)
    if imagen_bytes is None:
        return None

    try:
        url_publica = guardar_imagen_en_r2(zona, ciudad, lat, lon, imagen_bytes)
        return url_publica
    except Exception as e:
        logger.error(f"❌ No se pudo guardar la imagen: {e}")
        return None

# ============================================================
# VERSIÓN SÍNCRONA PARA FLASK
# ============================================================
def obtener_mapa_para_zona_sync(
    zona: str = None,
    ciudad: str = None,
    lat: float = None,
    lon: float = None
) -> Optional[str]:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(obtener_mapa_para_zona(zona, ciudad, lat, lon))
    except Exception as e:
        logger.error(f"Error en obtener_mapa_para_zona_sync: {e}")
        return None

# ============================================================
# LIMPIEZA DE CACHÉ (OPCIONAL)
# ============================================================
def limpiar_cache_expirado():
    try:
        client = get_r2_client()
    except ValueError as e:
        logger.error(f"❌ Error al obtener cliente R2: {e}")
        return

    try:
        response = client.list_objects_v2(Bucket=R2_BUCKET, Prefix='mapas/')
        if 'Contents' not in response:
            return
        ahora = datetime.now(timezone.utc)
        for obj in response['Contents']:
            last_modified = obj['LastModified']
            if ahora - last_modified > timedelta(hours=CACHE_EXPIRATION_HOURS):
                key = obj['Key']
                client.delete_object(Bucket=R2_BUCKET, Key=key)
                logger.info(f"🗑️ Eliminado caché expirado: {key}")
    except Exception as e:
        logger.error(f"❌ Error al limpiar caché: {e}")