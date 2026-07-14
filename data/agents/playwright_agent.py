import asyncio
import base64
import os
import sys
import json
import random
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright
import anthropic
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
from data.database import save_precio, init_db

load_dotenv(os.path.join(ROOT_DIR, '.env'))

USE_R2 = os.getenv("USE_R2", "false").lower() == "true"
LOCAL_SCREENSHOTS_DIR = os.path.join(ROOT_DIR, "data", "screenshots")

if USE_R2:
    import boto3
    from botocore.config import Config
    R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
    R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
    R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
    s3_client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("playwright_agent")

EXTRACTION_PROMPT = """
Eres un asistente que extrae información de capturas de pantalla de farmacias online.
Analiza la imagen y devuelve un JSON con esta estructura exacta:
{
    "medicamento": "nombre del medicamento que aparece en la imagen",
    "precio": "precio con formato XX.XX (solo números)",
    "farmacia": "nombre de la farmacia si está visible",
    "disponible": true/false,
    "fecha_captura": "YYYY-MM-DD HH:MM:SS"
}
Si no puedes leer algún campo, pon null. Solo responde con el JSON, sin comentarios adicionales.
"""

FARMACIAS = [
    {
        "nombre": "Farmacias del Ahorro",
        "url": "https://www.fahorro.com/",
        "price_selectors": [
            '[data-price-type="oldPrice"] .price',
            '[data-price-type="finalPrice"] .price',
            '.product-info-price .price',
            'span.price',
        ],
        "result_container": None,  # usaremos página completa
        "fallback_url": "https://www.fahorro.com/paracetamol-500-mg-oral-20-tabletas-marca-del-ahorro.html",
    },
    {
        "nombre": "Farmacias Benavides",
        "url": "https://www.benavides.com.mx/",
        "price_selectors": [".price"],
        "result_container": ".product-item:first-child",
        "fallback_url": "https://www.benavides.com.mx/perfalgan-paracetamol-1-ud-frasco-ampula",
    },
    {
        "nombre": "Probemedic",
        "url": "https://www.probemedic.mx/",
        "price_selectors": [".price"],
        "result_container": ".product",
        "fallback_url": None,
    },
]

def save_image(image_bytes: bytes, folder: str, filename: str) -> str:
    if USE_R2:
        key = f"{folder}/{filename}"
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=image_bytes,
            ContentType="image/png",
            ACL="public-read",
        )
        return f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{key}"
    else:
        local_path = Path(LOCAL_SCREENSHOTS_DIR) / folder / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(image_bytes)
        return str(local_path.absolute())

async def find_search_input(page):
    js_code = """
    () => {
        const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([disabled])'));
        const candidates = inputs.filter(input => {
            const style = window.getComputedStyle(input);
            return style.display !== 'none' && style.visibility !== 'hidden' && input.offsetWidth > 0 &&
                   (input.type === 'text' || input.type === 'search' || input.type === '' || input.type === null);
        });
        candidates.sort((a, b) => {
            let scoreA = 0, scoreB = 0;
            const attrs = ['id', 'name', 'placeholder', 'aria-label', 'className'];
            const keywords = ['buscar', 'search', 'q', 'query', 'busqueda'];
            for (const attr of attrs) {
                const valA = (a[attr] || '').toLowerCase();
                const valB = (b[attr] || '').toLowerCase();
                for (const kw of keywords) {
                    if (valA.includes(kw)) scoreA += 10;
                    if (valB.includes(kw)) scoreB += 10;
                }
            }
            if (a.type === 'search') scoreA += 5;
            if (b.type === 'search') scoreB += 5;
            return scoreB - scoreA;
        });
        if (candidates.length === 0) return null;
        const best = candidates[0];
        if (best.id) return `#${CSS.escape(best.id)}`;
        if (best.name) return `input[name="${best.name}"]`;
        if (best.className) {
            const cls = best.className.split(' ').filter(c => c).join('.');
            return `input.${cls}`;
        }
        const form = best.closest('form');
        if (form) {
            const index = Array.from(form.querySelectorAll('input')).indexOf(best) + 1;
            return `form input:nth-child(${index})`;
        }
        return 'input[type="text"]';
    }
    """
    selector = await page.evaluate(js_code)
    if selector:
        logger.info(f"   ✔ Buscador detectado: {selector}")
        return page.locator(selector).first
    logger.warning("   ⚠ No se pudo detectar un buscador automáticamente.")
    return None

async def tomar_screenshot(page, selector_contenedor: Optional[str] = None):
    if selector_contenedor:
        try:
            element = await page.wait_for_selector(selector_contenedor, timeout=10000)
            return await element.screenshot()
        except Exception:
            logger.warning("No se encontró el contenedor, usando página completa")
    return await page.screenshot(full_page=False)

async def extraer_precio_directo(page, selectors: list) -> Optional[float]:
    """Intenta extraer el precio directamente del DOM usando selectores CSS."""
    for selector in selectors:
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                texto = await element.inner_text()
                limpio = re.sub(r'[^\d.]', '', texto)
                if limpio:
                    return float(limpio)
        except Exception:
            continue
    return None

def extraer_precio_regex(texto: str) -> Optional[float]:
    patrones = [
        r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))',
        r'\$\s*(\d+(?:\.\d{2})?)',
        r'(\d+\.\d{2})\s*\$',
    ]
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            precio_str = match.group(1).replace(',', '')
            return float(precio_str)
    return None

async def extraer_datos(page, image_bytes: bytes, farmacia_nombre: str, price_selectors: list) -> Dict[str, Any]:
    """
    Extrae datos en orden de prioridad:
    1. Extracción directa con selectores CSS (solo precio, el resto por Claude)
    2. Claude Vision (imagen)
    3. Regex sobre el texto visible
    """
    datos = {}
    precio_directo = await extraer_precio_directo(page, price_selectors)
    if precio_directo:
        logger.info(f"   Precio extraído directamente del DOM: ${precio_directo}")
        datos["precio"] = str(precio_directo)
    else:
        # Intentar Claude
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        try:
            response = claude.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image,
                                },
                            },
                            {"type": "text", "text": EXTRACTION_PROMPT},
                        ],
                    }
                ],
            )
            texto = response.content[0].text
            texto = texto.strip("`").replace("json\n", "").replace("\n`", "")
            datos = json.loads(texto)
        except Exception as e:
            logger.error(f"Error en Claude Vision: {e}")
            datos = {"error": str(e)}

        # Si Claude no devolvió precio, regex
        if not datos.get("precio") or datos.get("precio") == "null":
            logger.info("   Claude no extrajo precio, intentando regex...")
            try:
                texto_pagina = await page.inner_text("body")
                precio_regex = extraer_precio_regex(texto_pagina)
                if precio_regex:
                    datos["precio"] = str(precio_regex)
                    logger.info(f"   Regex encontró precio: ${precio_regex}")
            except Exception as e:
                logger.warning(f"Error al extraer texto: {e}")

    # Nombre y farmacia
    if not datos.get("farmacia"):
        datos["farmacia"] = farmacia_nombre
    if not datos.get("medicamento"):
        datos["medicamento"] = "paracetamol"  # asumimos el buscado

    # Mantener el precio directo si ya lo teníamos
    if precio_directo and not datos.get("precio"):
        datos["precio"] = str(precio_directo)

    return datos

async def guardar_en_db(datos: dict, fuente: str, imagen_url: str):
    try:
        precio = datos.get("precio")
        if precio is None or precio == "null":
            logger.warning("No se extrajo precio, omitiendo guardado.")
            return
        if isinstance(precio, str):
            precio = float(precio.replace(",", "").strip())
        registro = {
            "medicamento": datos.get("medicamento", "desconocido").lower(),
            "nombre_raw": datos.get("medicamento"),
            "farmacia": datos.get("farmacia"),
            "precio": precio,
            "url": None,
            "imagen_url": imagen_url,
            "fuente": fuente,
            "fecha": datetime.now(timezone.utc).isoformat(),
            "ciudad": None,
            "precio_promo": None,
            "vigencia": None,
        }
        save_precio(registro)
        logger.info(f"Guardado: {registro['medicamento']} en {registro['farmacia']} - ${registro['precio']}")
    except Exception as e:
        logger.error(f"Error guardando en BD: {e}")

async def capturar_precio(farmacia: dict, medicamento: str, headless: bool = True) -> Optional[Dict]:
    nombre = farmacia["nombre"]
    logger.info(f"⏳ Procesando {nombre}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Navegar a la página principal
            await page.goto(farmacia["url"], timeout=30000)
            await page.wait_for_load_state('networkidle', timeout=10000)
            await asyncio.sleep(random.uniform(2, 4))

            search_input = await find_search_input(page)
            if search_input:
                await search_input.fill(medicamento)
                await search_input.press("Enter")
                # Esperar a que aparezca algo con $ o el primer selector de precio
                try:
                    await page.wait_for_selector(farmacia["price_selectors"][0], timeout=10000)
                except Exception:
                    logger.warning("No apareció el selector de precio esperado.")
                await asyncio.sleep(1)
            else:
                logger.info("   Usando URL de producto de respaldo...")
                if farmacia.get("fallback_url"):
                    await page.goto(farmacia["fallback_url"], timeout=30000)
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    await asyncio.sleep(2)
                else:
                    logger.error(f"No hay URL de respaldo para {nombre}. Omitiendo.")
                    await browser.close()
                    return None

            # Screenshot
            screenshot_bytes = await tomar_screenshot(page, farmacia.get("result_container"))

            # Guardar imagen
            fecha_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            folder = nombre.lower().replace(" ", "_")
            filename = f"{medicamento.lower()}/{fecha_str}.png"
            imagen_url = save_image(screenshot_bytes, folder, filename)

            # Extraer datos híbridos
            datos = await extraer_datos(page, screenshot_bytes, nombre, farmacia["price_selectors"])
            await guardar_en_db(datos, fuente="agente_playwright", imagen_url=imagen_url)

            await browser.close()
            logger.info(f"✅ {nombre}: éxito")
            return datos

        except Exception as e:
            logger.error(f"❌ Error en {nombre}: {e}")
            await browser.close()
            return None

async def main(medicamento: str):
    init_db()
    logger.info(f"🚀 Iniciando agente Playwright para: {medicamento}")

    resultados = []
    for farmacia in FARMACIAS:
        resultado = await capturar_precio(farmacia, medicamento, headless=True)
        resultados.append({
            "farmacia": farmacia["nombre"],
            "exito": resultado is not None,
            "datos": resultado
        })

    for r in resultados:
        estado = "✅" if r["exito"] else "❌"
        logger.info(f"{estado} {r['farmacia']}: {r['datos']}")

    return resultados

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python data/agents/playwright_agent.py <medicamento>")
        sys.exit(1)
    medicamento = sys.argv[1]
    asyncio.run(main(medicamento))