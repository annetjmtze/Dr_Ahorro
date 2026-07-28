import os
import asyncio
import random
import hashlib
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
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_BUCKET = os.getenv("R2_BUCKET", "dr-ahorro-screenshots")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

CACHE_EXPIRATION_HOURS = 6

# Logs seguros (validando que no sean None)
if R2_ACCESS_KEY:
    logger.info(f"🔑 R2_ACCESS_KEY configurada (primeros 4 caracteres: {R2_ACCESS_KEY[:4]}...)")
else:
    logger.warning("⚠️ R2_ACCESS_KEY no está definida en el entorno")

if R2_ENDPOINT:
    logger.info(f"🔗 R2_ENDPOINT configurado: {R2_ENDPOINT}")
else:
    logger.warning("⚠️ R2_ENDPOINT no está definido en el entorno")

if R2_PUBLIC_URL:
    logger.info(f"🌐 R2_PUBLIC_URL configurada: {R2_PUBLIC_URL}")
else:
    logger.warning("⚠️ R2_PUBLIC_URL no está definida en el entorno")

# ============================================================
# CLIENTE R2 CON VALIDACIÓN
# ============================================================
def get_r2_client():
    """Retorna un cliente boto3 para R2, validando credenciales."""
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
# FUNCIONES AUXILIARES
# ============================================================
def generar_key_zona(zona: str) -> str:
    """Genera una clave única para la zona, usando hash para evitar caracteres especiales."""
    zona_limpia = zona.lower().strip().replace(' ', '_').replace(',', '').replace('.', '')
    hash_obj = hashlib.md5(zona.encode('utf-8')).hexdigest()[:8]
    return f"mapas/{zona_limpia}_{hash_obj}.png"

def obtener_imagen_cacheada(zona: str) -> Optional[Tuple[str, datetime]]:
    """
    Verifica si existe una imagen para la zona en R2 con menos de 6 horas.
    Retorna (url_publica, fecha_creacion) o None.
    """
    try:
        client = get_r2_client()
    except ValueError as e:
        logger.error(f"❌ Error al obtener cliente R2: {e}")
        return None

    key = generar_key_zona(zona)
    try:
        head = client.head_object(Bucket=R2_BUCKET, Key=key)
        last_modified = head['LastModified']
        ahora = datetime.now(timezone.utc)
        if ahora - last_modified < timedelta(hours=CACHE_EXPIRATION_HOURS):
            url_publica = f"{R2_PUBLIC_URL}/{key}"
            return (url_publica, last_modified)
        else:
            logger.info(f"🗑️ Caché expirado para {zona} (última modificación: {last_modified})")
            return None
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info(f"📭 No hay caché para {zona}")
        else:
            logger.error(f"❌ Error al verificar caché en R2: {e}")
        return None

def guardar_imagen_en_r2(zona: str, imagen_bytes: bytes) -> str:
    """Guarda la imagen en R2 y retorna la URL pública."""
    try:
        client = get_r2_client()
    except ValueError as e:
        logger.error(f"❌ Error al obtener cliente R2: {e}")
        raise

    key = generar_key_zona(zona)
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
        logger.error(f"❌ Error al guardar imagen en R2: {e}")
        raise

# ============================================================
# CAPTURA DE MAPA CON PLAYWRIGHT
# ============================================================
async def capturar_mapa_farmacias(zona: str) -> Optional[bytes]:
    """
    Abre Google Maps con Playwright, espera a que carguen los pines y captura el mapa.
    Retorna los bytes de la imagen o None si falla.
    """
    try:
        query = f"farmacias cerca de {zona} México"
        url = f"https://www.google.com/maps/search/{query}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 800, "height": 600},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle")

            try:
                # Esperar a que el mapa esté listo
                await page.wait_for_selector('[role="main"]', timeout=10000)
                await asyncio.sleep(random.uniform(3, 5))
            except Exception as e:
                logger.warning(f"⚠️ No se pudo detectar el mapa correctamente: {e}")

            # Capturar solo la parte derecha (mapa)
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
# FUNCIÓN PRINCIPAL (VERSIÓN ASÍNCRONA)
# ============================================================
async def obtener_mapa_para_zona(zona: str) -> Optional[str]:
    """
    Función principal: retorna la URL pública de la imagen del mapa.
    Si está en caché y es reciente, la devuelve; si no, la genera y guarda.
    Retorna None si falla.
    """
    # Verificar caché
    cached = obtener_imagen_cacheada(zona)
    if cached:
        url, fecha = cached
        logger.info(f"♻️ Usando caché para {zona} (generado: {fecha})")
        return url

    # Si no está en caché o expiró, generar nuevo
    logger.info(f"🆕 Generando nuevo mapa para {zona}")
    imagen_bytes = await capturar_mapa_farmacias(zona)
    if imagen_bytes is None:
        return None

    try:
        url_publica = guardar_imagen_en_r2(zona, imagen_bytes)
        return url_publica
    except Exception as e:
        logger.error(f"❌ No se pudo guardar la imagen en R2: {e}")
        return None

# ============================================================
# VERSIÓN SÍNCRONA PARA USAR EN FLASK
# ============================================================
def obtener_mapa_para_zona_sync(zona: str) -> Optional[str]:
    """Versión síncrona de obtener_mapa_para_zona."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(obtener_mapa_para_zona(zona))
    except Exception as e:
        logger.error(f"Error en obtener_mapa_para_zona_sync: {e}")
        return None

# ============================================================
# LIMPIEZA DE CACHÉ (OPCIONAL)
# ============================================================
def limpiar_cache_expirado():
    """Elimina objetos en R2 que tengan más de 6 horas."""
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