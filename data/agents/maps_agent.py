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
# CONFIGURACIÓN DE R2 DESDE ENTORNO (nombres que tienes en Railway)
# ============================================================
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT_URL")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "dr-ahorro-screenshots")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

CACHE_EXPIRATION_HOURS = 6

# Logs seguros
if R2_ACCESS_KEY:
    logger.info(f"🔑 R2_ACCESS_KEY configurada (primeros 4: {R2_ACCESS_KEY[:4]}...)")
else:
    logger.warning("⚠️ R2_ACCESS_KEY no está definida")

if R2_PUBLIC_URL:
    logger.info(f"🌐 R2_PUBLIC_URL: {R2_PUBLIC_URL}")
else:
    logger.warning("⚠️ R2_PUBLIC_URL no está definida")

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

def generar_key_zona(zona: str, ciudad: str = "") -> str:
    """Genera una clave única para la zona+ciudad usando hash."""
    base = f"{zona}_{ciudad}".lower().strip()
    base_limpia = base.replace(' ', '_').replace(',', '').replace('.', '')
    hash_obj = hashlib.md5(base.encode('utf-8')).hexdigest()[:8]
    return f"mapas/{base_limpia}_{hash_obj}.png"

def obtener_imagen_cacheada(zona: str, ciudad: str = "Ciudad de México") -> Optional[Tuple[str, datetime]]:
    try:
        client = get_r2_client()
    except ValueError as e:
        logger.error(f"❌ Error al obtener cliente R2: {e}")
        return None

    key = generar_key_zona(zona, ciudad)
    try:
        head = client.head_object(Bucket=R2_BUCKET, Key=key)
        last_modified = head['LastModified']
        ahora = datetime.now(timezone.utc)
        if ahora - last_modified < timedelta(hours=CACHE_EXPIRATION_HOURS):
            url_publica = f"{R2_PUBLIC_URL}/{key}"
            return (url_publica, last_modified)
        else:
            logger.info(f"🗑️ Caché expirado para {zona}, {ciudad}")
            return None
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info(f"📭 No hay caché para {zona}, {ciudad}")
        else:
            logger.error(f"❌ Error al verificar caché: {e}")
        return None

def guardar_imagen_en_r2(zona: str, ciudad: str, imagen_bytes: bytes) -> str:
    try:
        client = get_r2_client()
    except ValueError as e:
        logger.error(f"❌ Error al obtener cliente R2: {e}")
        raise

    key = generar_key_zona(zona, ciudad)
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

async def capturar_mapa_farmacias(zona: str, ciudad: str = "Ciudad de México") -> Optional[bytes]:
    try:
        # 🔥 Aquí usamos la ciudad en la búsqueda
        query = f"farmacias cerca de {zona}, {ciudad}"
        url = f"https://www.google.com/maps/search/{query}"

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
                logger.warning(f"⚠️ No se pudo detectar el mapa: {e}")

            screenshot = await page.screenshot(
                clip={"x": 350, "y": 0, "width": 450, "height": 600},
                type='png'
            )
            await browser.close()
            return screenshot
    except Exception as e:
        logger.error(f"❌ Error en capturar_mapa_farmacias: {e}")
        return None

async def obtener_mapa_para_zona(zona: str, ciudad: str = "Ciudad de México") -> Optional[str]:
    cached = obtener_imagen_cacheada(zona, ciudad)
    if cached:
        url, fecha = cached
        logger.info(f"♻️ Usando caché para {zona}, {ciudad} (generado: {fecha})")
        return url

    logger.info(f"🆕 Generando nuevo mapa para {zona}, {ciudad}")
    imagen_bytes = await capturar_mapa_farmacias(zona, ciudad)
    if imagen_bytes is None:
        return None

    try:
        url_publica = guardar_imagen_en_r2(zona, ciudad, imagen_bytes)
        return url_publica
    except Exception as e:
        logger.error(f"❌ No se pudo guardar la imagen: {e}")
        return None

def obtener_mapa_para_zona_sync(zona: str, ciudad: str = "Ciudad de México") -> Optional[str]:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(obtener_mapa_para_zona(zona, ciudad))
    except Exception as e:
        logger.error(f"Error en obtener_mapa_para_zona_sync: {e}")
        return None

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