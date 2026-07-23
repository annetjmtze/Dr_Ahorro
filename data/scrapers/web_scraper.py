import requests
from bs4 import BeautifulSoup
import json
import re
import logging
from datetime import datetime
import sys
import os
from urllib.parse import urlparse

# ── Cargar variables de entorno ──
from dotenv import load_dotenv
load_dotenv()  # Busca .env en la raíz del proyecto

# ── Configurar logging ──
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("web_scraper")

# ── Asegurar que la raíz del proyecto está en sys.path ──
# Esto funciona tanto localmente como en Railway (donde la raíz es /app)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ── Importar módulos del proyecto ──
from data.storage.r2_client import save_image, USE_R2
from data.database import save_precio, init_db, contar_por_fuente

# ──────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PARA TOMAR SCREENSHOT CON PLAYWRIGHT (SYNC)
# ──────────────────────────────────────────────────────────────────────────────
def tomar_screenshot_sync(url):
    """
    Toma un screenshot de la URL usando Playwright (modo síncrono).
    Retorna los bytes de la imagen o None si falla.
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(2000)  # esperar carga
            screenshot_bytes = page.screenshot(full_page=True)
            browser.close()
            return screenshot_bytes
    except Exception as e:
        logger.error(f"❌ Error al tomar screenshot de {url}: {e}")
        return None

# ──────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ──────────────────────────────────────────────────────────────────────────────
def limpiar_precio(texto):
    """Limpia caracteres no numéricos y convierte a float."""
    if not texto:
        return None
    limpio = re.sub(r'[^\d.]', '', texto)
    try:
        return float(limpio)
    except ValueError:
        return None

def validar_url(url):
    """Verifica que la URL sea válida."""
    if not url:
        return False
    try:
        r = urlparse(url)
        return r.scheme in ('http', 'https') and bool(r.netloc)
    except:
        return False

# ──────────────────────────────────────────────────────────────────────────────
# GUARDAR EN BD CON IMAGEN_URL
# ──────────────────────────────────────────────────────────────────────────────
def guardar_resultado(datos):
    try:
        if 'fuente' not in datos or datos['fuente'] is None:
            datos['fuente'] = 'farmacia'
        
        if datos.get('url_producto') and not validar_url(datos['url_producto']):
            logger.warning(f"URL inválida: {datos['url_producto']} - se guardará sin URL")
            datos['url_producto'] = None

        registro = {
            "medicamento": datos.get("medicamento_buscado", "desconocido"),
            "nombre_raw": datos.get("nombre_en_farmacia"),
            "farmacia": datos.get("farmacia"),
            "ciudad": None,
            "precio": datos.get("precio"),
            "precio_promo": datos.get("precio_promo"),
            "vigencia": datos.get("vigencia_promo"),
            "url": datos.get("url_producto"),
            "fuente": datos.get("fuente"),
            "fecha": datos.get("fecha_consulta", datetime.now().isoformat()),
            "imagen_url": datos.get("imagen_url")   # <--- CLAVE
        }
        save_precio(registro)
        logger.info(f"💾 Guardado en BD: {registro['farmacia']} - ${registro['precio']} (fuente: {registro['fuente']})")
        if registro.get("imagen_url"):
            logger.info(f"   📸 Imagen: {registro['imagen_url']}")
    except Exception as e:
        logger.error(f"⚠️ Error al guardar en BD: {e}")

# ──────────────────────────────────────────────────────────────────────────────
# SCRAPERS ESPECÍFICOS
# ──────────────────────────────────────────────────────────────────────────────

def scrape_ahorro(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-MX,es;q=0.9'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        price_elem = soup.select_one('[data-price-type="oldPrice"] .price')
        if not price_elem:
            price_elem = soup.select_one('[data-price-type="finalPrice"] .price')
        if not price_elem:
            price_elem = soup.select_one('.product-info-price .price')
        if not price_elem:
            price_elem = soup.select_one('span.price')
        precio = limpiar_precio(price_elem.text) if price_elem else None

        promo_elem = soup.select_one('.special-price .price')
        precio_promo = limpiar_precio(promo_elem.text) if promo_elem else None
        vigencia = None

        name_elem = soup.select_one('h1.page-title span')
        if not name_elem:
            name_elem = soup.select_one('h1 span')
        nombre = name_elem.text.strip() if name_elem else "Paracetamol 500 mg"

        # Screenshot y subida a R2
        screenshot_bytes = tomar_screenshot_sync(url)
        imagen_url = None
        if screenshot_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder = "web_scraper/ahorro"
            filename = f"paracetamol_{timestamp}.png"
            imagen_url = save_image(screenshot_bytes, folder, filename)

        resultado = {
            "medicamento_buscado": "paracetamol",
            "nombre_en_farmacia": nombre,
            "farmacia": "Farmacias del Ahorro",
            "precio": precio,
            "precio_promo": precio_promo,
            "vigencia_promo": vigencia,
            "url_producto": url,
            "fuente": "farmacia",
            "fecha_consulta": datetime.now().isoformat(),
            "imagen_url": imagen_url
        }

        if precio is not None:
            guardar_resultado(resultado)
        return resultado
    except Exception as e:
        logger.error(f"❌ Error en Farmacias del Ahorro: {e}")
        return None

def scrape_benavides(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-MX,es;q=0.9'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        price_elem = soup.select_one('.price')
        if not price_elem:
            price_elem = soup.select_one('.product-info-price .price')
        if not price_elem:
            price_elem = soup.select_one('[data-price-type="finalPrice"] .price')
        precio = limpiar_precio(price_elem.text) if price_elem else None

        if not precio:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'dl4Objects' in script.string:
                    match = re.search(r'dl4Objects\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            for obj in data:
                                if obj.get('event') == 'view_item' and obj.get('pageType') == 'product':
                                    items = obj.get('ecommerce', {}).get('items', [])
                                    if items:
                                        precio = float(items[0].get('price', 0))
                                        break
                        except:
                            pass
                    break

        precio_promo = None
        vigencia = None

        name_elem = soup.select_one('h1.page-title span')
        if not name_elem:
            name_elem = soup.select_one('h1 span')
        nombre = name_elem.text.strip() if name_elem else "Perfalgan Paracetamol"

        # Screenshot y subida a R2
        screenshot_bytes = tomar_screenshot_sync(url)
        imagen_url = None
        if screenshot_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder = "web_scraper/benavides"
            filename = f"paracetamol_{timestamp}.png"
            imagen_url = save_image(screenshot_bytes, folder, filename)

        resultado = {
            "medicamento_buscado": "paracetamol",
            "nombre_en_farmacia": nombre,
            "farmacia": "Farmacias Benavides",
            "precio": precio,
            "precio_promo": precio_promo,
            "vigencia_promo": vigencia,
            "url_producto": url,
            "fuente": "farmacia",
            "fecha_consulta": datetime.now().isoformat(),
            "imagen_url": imagen_url
        }

        if precio is not None:
            guardar_resultado(resultado)
        return resultado
    except Exception as e:
        logger.error(f"❌ Error en Farmacias Benavides: {e}")
        return None

def scrape_probemedic(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar precio
        price_elem = soup.select_one('.product-price, .price, .special-price, .regular-price')
        if price_elem:
            precio = limpiar_precio(price_elem.text)
        else:
            price_text = soup.select_one('.product-info') or soup.select_one('.product-details')
            if price_text:
                match = re.search(r'\$(\d+\.\d{2})', price_text.get_text())
                precio = float(match.group(1)) if match else None
            else:
                precio = None

        title = soup.find('title')
        nombre = title.text.strip() if title else "Paracetamol 500mg 10 tabletas"

        # Detectar medicamento
        medicamento = "desconocido"
        if "paracetamol" in nombre.lower():
            medicamento = "paracetamol"
        elif "ibuprofeno" in nombre.lower():
            medicamento = "ibuprofeno"
        elif "fluoxetina" in nombre.lower():
            medicamento = "fluoxetina"
        elif "diclofenaco" in nombre.lower():
            medicamento = "diclofenaco"
        elif "loratadina" in nombre.lower():
            medicamento = "loratadina"
        elif "metformina" in nombre.lower():
            medicamento = "metformina"
        elif "celecoxib" in nombre.lower():
            medicamento = "celecoxib"

        # Screenshot y subida a R2
        screenshot_bytes = tomar_screenshot_sync(url)
        imagen_url = None
        if screenshot_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder = "web_scraper/probemedic"
            filename = f"{medicamento}_{timestamp}.png"
            imagen_url = save_image(screenshot_bytes, folder, filename)

        resultado = {
            "medicamento_buscado": medicamento,
            "nombre_en_farmacia": nombre,
            "farmacia": "Probemedic",
            "precio": precio,
            "precio_promo": None,
            "vigencia_promo": None,
            "url_producto": url,
            "fuente": "farmacia",
            "fecha_consulta": datetime.now().isoformat(),
            "imagen_url": imagen_url
        }

        if precio is not None:
            guardar_resultado(resultado)
        return resultado
    except Exception as e:
        logger.error(f"❌ Error en Probemedic: {e}")
        return None

# ──────────────────────────────────────────────────────────────────────────────
# EJECUCIÓN PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────
def main():
    init_db()
    logger.info("📦 Base de datos inicializada")

    urls_probemedic = [
        "https://www.probemedic.mx/paracetamol-500mg-10-tabletas.html",
        "https://www.probemedic.mx/ibuprofeno-800-mg-10-tabletas.html",
        "https://www.probemedic.mx/fluoxetina-20-mg-14-capsulas.html",
        "https://www.probemedic.mx/diclofenaco-100-mg-20-tabletas.html",
        "https://www.probemedic.mx/loratadina-10-mg-10-tabletas.html",
        "https://www.probemedic.mx/metformina-850-mg-30-tabletas.html",
        "https://www.probemedic.mx/celecoxib-200-mg-10-capsulas.html"
    ]

    urls_otras = {
        "ahorro": "https://www.fahorro.com/paracetamol-500-mg-oral-20-tabletas-marca-del-ahorro.html",
        "benavides": "https://www.benavides.com.mx/perfalgan-paracetamol-1-ud-frasco-ampula"
    }

    resultados = []

    logger.info("🔍 Scrapeando Farmacias del Ahorro...")
    res_ahorro = scrape_ahorro(urls_otras["ahorro"])
    if res_ahorro:
        resultados.append(res_ahorro)

    logger.info("🔍 Scrapeando Farmacias Benavides...")
    res_benav = scrape_benavides(urls_otras["benavides"])
    if res_benav:
        resultados.append(res_benav)

    logger.info("🔍 Scrapeando Probemedic...")
    for url in urls_probemedic:
        logger.info(f"  - {url.split('/')[-1]}...")
        res_prob = scrape_probemedic(url)
        if res_prob:
            resultados.append(res_prob)
            logger.info(f"    ✅ OK: ${res_prob['precio']}")
        else:
            logger.warning(f"    ❌ Falló")

    if resultados:
        os.makedirs("data/scrapers", exist_ok=True)
        with open("data/scrapers/resultados_farmacias.json", "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        logger.info(f"📁 {len(resultados)} resultados guardados en data/scrapers/resultados_farmacias.json")
        logger.info("📋 Resumen:")
        for r in resultados:
            logger.info(f"  - {r['farmacia']}: ${r['precio']} - {r['nombre_en_farmacia']} (fuente: {r['fuente']})")
    else:
        logger.warning("❌ No se obtuvo ningún resultado.")

    try:
        fuente_counts = contar_por_fuente()
        if fuente_counts:
            logger.info("📊 Registros en BD por fuente:")
            for fuente, total in fuente_counts.items():
                logger.info(f"  {fuente}: {total}")
        else:
            logger.info("  No hay registros.")
    except Exception as e:
        logger.error(f"Error al contar por fuente: {e}")

if __name__ == "__main__":
    main()