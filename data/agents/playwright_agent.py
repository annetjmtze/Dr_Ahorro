import os
import sys
import asyncio
import base64
import json
import random
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

# ── Configurar logging a stdout ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("playwright_agent")

# ── Ruta a Google Chrome (si está instalado) ──
CHROME_PATH = "/usr/bin/google-chrome-stable"

# ── Importar dependencias ──
from playwright.async_api import async_playwright
import anthropic
from dotenv import load_dotenv

# ── Configurar entorno ──────────────────────────────────────────────
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
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

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
        "result_container": None,
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
    # ── NUEVAS FARMACIAS ────────────────────────────────
    {
        "nombre": "Farmacias Similares",
        "url": "https://www.farmaciasdesimilares.com/",
        "price_selectors": [
            ".price-box .price",
            ".price",
            ".product-price",
        ],
        "result_container": ".product",
        "fallback_url": "https://www.farmaciasdesimilares.com/paracetamol-500-mg",
    },
        {
        "nombre": "Farmacias San Pablo",
        "url": "https://www.farmaciasanpablo.com.mx/",   # página principal (puede bloquear)
        "price_selectors": [
            ".price-box .price",
            ".product-price",
            "span.price",
            ".regular-price",
        ],
        "result_container": None,
        # Sustituye por una URL de producto que muestre precio (ej. paracetamol)
        "fallback_url": "https://www.farmaciasanpablo.com.mx/medicamentos/genericos/m---n---o---p/paracetamol-500-0-mg/p/000000000070007368",
    },
    {
        "nombre": "Farmacia La Paz",
        "url": "https://farmacialapaz.com.mx/",
        "price_selectors": [
            ".price-special",
            ".product-price",
            "span.price",
        ],
        "result_container": None,
        "fallback_url": "https://farmacialapaz.com.mx/paracetamol-500-mg",
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

async def extraer_precio_directo(page, selectors: list) -> Optional[float]:
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

def extraer_precio_desde_html(html: str) -> Optional[float]:
    patrones = [
        r'"price"\s*:\s*"?([\d.]+)"?',
        r'property="product:price:amount"\s*content="([\d.]+)"',
        r'data-price-amount="([\d.]+)"',
        r'itemprop="price"\s*content="([\d.]+)"',
    ]
    for patron in patrones:
        match = re.search(patron, html)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    return None

async def extraer_datos(page, image_bytes: bytes, farmacia_nombre: str, price_selectors: list) -> Dict[str, Any]:
    datos = {}
    precio = await extraer_precio_directo(page, price_selectors)
    if precio:
        logger.info(f"   Precio extraído directamente del DOM: ${precio}")
    else:
        # Claude Vision (solo si hay API key)
        if claude:
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
                precio_claude = datos.get("precio")
                if precio_claude and precio_claude != "null":
                    if isinstance(precio_claude, str):
                        precio = float(precio_claude.replace(",", "").strip())
                    else:
                        precio = float(precio_claude)
                    logger.info(f"   Precio extraído por Claude: ${precio}")
            except Exception as e:
                logger.warning(f"Error en Claude: {e}")
        else:
            logger.warning("   Claude API key no configurada. Saltando visión.")

    if not precio:
        try:
            texto_pagina = await page.inner_text("body")
            precio = extraer_precio_regex(texto_pagina)
            if precio:
                logger.info(f"   Regex encontró precio: ${precio}")
        except Exception as e:
            logger.warning(f"Error regex: {e}")

    if not precio:
        logger.info("   Intentando extraer precio desde HTML crudo (JSON-LD)...")
        html = await page.content()
        precio = extraer_precio_desde_html(html)
        if precio:
            logger.info(f"   Precio encontrado en HTML crudo: ${precio}")

    datos["precio"] = str(precio) if precio else None
    if not datos.get("farmacia"):
        datos["farmacia"] = farmacia_nombre
    if not datos.get("medicamento"):
        datos["medicamento"] = "paracetamol"
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
        # ── Usar Chrome con executable_path (si existe) ──
        launch_options = {
            "headless": headless,
            "args": ["--disable-blink-features=AutomationControlled"]
        }
        # Intentar usar Google Chrome si está instalado
        if os.path.exists(CHROME_PATH):
            launch_options["executable_path"] = CHROME_PATH
            logger.info(f"   Usando Google Chrome desde {CHROME_PATH}")
        else:
            logger.warning(f"   Google Chrome no encontrado en {CHROME_PATH}, usando Chromium por defecto.")
            # Si no está, usamos channel="chrome" como fallback (puede funcionar si Chrome está en otro lugar)
            # Pero mejor usar playwright por defecto (sin channel) que es Chromium
            # No especificamos channel para que use Chromium integrado.

        browser = await p.chromium.launch(**launch_options)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # ── Navegar a la página principal ──
            await page.goto(farmacia["url"], timeout=30000)
            # Cambiar de networkidle a domcontentloaded para evitar timeouts
            await page.wait_for_load_state('domcontentloaded', timeout=15000)
            await asyncio.sleep(random.uniform(2, 4))

            search_input = await find_search_input(page)
            if search_input:
                await search_input.fill(medicamento)
                await search_input.press("Enter")
                # Esperar a que aparezca algún selector de precio
                for sel in farmacia["price_selectors"]:
                    try:
                        await page.wait_for_selector(sel, timeout=5000)
                        break
                    except Exception:
                        continue
                await asyncio.sleep(1)
            else:
                logger.info("   Usando URL de producto de respaldo...")
                if farmacia.get("fallback_url"):
                    await page.goto(farmacia["fallback_url"], timeout=30000)
                    await page.wait_for_load_state('domcontentloaded', timeout=15000)
                    await asyncio.sleep(random.uniform(2, 3))
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