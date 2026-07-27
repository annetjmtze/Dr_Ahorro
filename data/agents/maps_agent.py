import os
import asyncio
import random
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
import logging

from playwright.async_api import async_playwright
import boto3  # para interactuar con R2 (compatible con S3)
from botocore.exceptions import ClientError

from data.database import get_usuario  # para obtener la zona del usuario

logger = logging.getLogger(__name__)

# Configuración de R2 desde variables de entorno
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")  # ej: https://<account>.r2.cloudflarestorage.com
R2_BUCKET = os.getenv("R2_BUCKET", "dr-ahorro-screenshots")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")  # URL pública del bucket, ej: https://dr-ahorro-screenshots.r2.cloudflarestorage.com

# Tiempo de validez del caché (6 horas)
CACHE_EXPIRATION_HOURS = 6

# Inicializar cliente S3 para R2
def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )

def generar_key_zona(zona: str) -> str:
    """Genera una clave única para la zona, usando hash para evitar caracteres especiales."""
    # Limpiar la zona para usarla en nombre de archivo
    zona_limpia = zona.lower().strip().replace(' ', '_').replace(',', '').replace('.', '')
    # Añadir un hash corto para evitar colisiones
    hash_obj = hashlib.md5(zona.encode('utf-8')).hexdigest()[:8]
    return f"mapas/{zona_limpia}_{hash_obj}.png"

def obtener_imagen_cacheada(zona: str) -> Optional[Tuple[str, datetime]]:
    """
    Verifica si existe una imagen para la zona en R2 con menos de 6 horas.
    Retorna (url_publica, fecha_creacion) o None.
    """
    client = get_r2_client()
    key = generar_key_zona(zona)
    try:
        # Obtener metadatos del objeto para conocer la fecha de creación
        head = client.head_object(Bucket=R2_BUCKET, Key=key)
        last_modified = head['LastModified']  # datetime UTC
        ahora = datetime.now(timezone.utc)
        if ahora - last_modified < timedelta(hours=CACHE_EXPIRATION_HOURS):
            url_publica = f"{R2_PUBLIC_URL}/{key}"
            return (url_publica, last_modified)
        else:
            logger.info(f"🗑️ Caché expirado para {zona} (última modificación: {last_modified})")
            # Opcional: eliminar el objeto si expiró
            # client.delete_object(Bucket=R2_BUCKET, Key=key)
            return None
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info(f"📭 No hay caché para {zona}")
        else:
            logger.error(f"❌ Error al verificar caché en R2: {e}")
        return None

def guardar_imagen_en_r2(zona: str, imagen_bytes: bytes) -> str:
    """Guarda la imagen en R2 y retorna la URL pública."""
    client = get_r2_client()
    key = generar_key_zona(zona)
    try:
        client.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=imagen_bytes,
            ContentType='image/png',
            ACL='public-read'  # Asegura que sea público
        )
        url_publica = f"{R2_PUBLIC_URL}/{key}"
        logger.info(f"✅ Imagen guardada en R2: {url_publica}")
        return url_publica
    except Exception as e:
        logger.error(f"❌ Error al guardar imagen en R2: {e}")
        raise

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
            
            # Esperar a que aparezca el mapa (puede ser un selector del canvas o algún elemento del mapa)
            # El selector '[data-value="Farmacias"]' es un intento, pero puede no ser fiable.
            # Usaremos un enfoque más robusto: esperar a que el contenedor del mapa tenga clases específicas.
            # En su lugar, esperamos a que aparezca el div del mapa con un timeout.
            try:
                await page.wait_for_selector('[role="main"]', timeout=10000)  # El contenedor principal de Maps
                # También podemos esperar a que haya pines en el mapa (pero los pines no tienen selectores fijos)
                # Damos un tiempo extra para que carguen los pines
                await asyncio.sleep(random.uniform(3, 5))
            except Exception as e:
                logger.warning(f"⚠️ No se pudo detectar el mapa correctamente: {e}")
                # Aún así intentamos capturar
            
            # Capturar solo la parte derecha (mapa)
            # En la vista de escritorio, el mapa suele estar a la derecha, pero puede variar.
            # Usamos un recorte fijo: x=350, width=450 para cubrir el mapa en la mayoría de casos.
            # Podríamos mejorar calculando la posición del elemento del mapa.
            screenshot = await page.screenshot(
                clip={"x": 350, "y": 0, "width": 450, "height": 600},
                type='png'
            )
            await browser.close()
            return screenshot
    except Exception as e:
        logger.error(f"❌ Error en capturar_mapa_farmacias: {e}")
        return None

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

# Función de limpieza (opcional) para borrar caché viejo
def limpiar_cache_expirado():
    """
    Elimina objetos en R2 que tengan más de 6 horas.
    Se podría llamar periódicamente con un cron job.
    """
    client = get_r2_client()
    # Listar objetos en el prefijo 'mapas/'
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

def obtener_mapa_para_zona_sync(zona: str) -> Optional[str]:
    """Versión síncrona de obtener_mapa_para_zona."""
    try:
        return asyncio.run(obtener_mapa_para_zona(zona))
    except Exception as e:
        logger.error(f"Error en obtener_mapa_para_zona_sync: {e}")
        return None