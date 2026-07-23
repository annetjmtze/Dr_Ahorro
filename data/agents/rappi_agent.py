import asyncio
import os
import sys
import json
import re
import random
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)
from data.database import save_precio

load_dotenv(os.path.join(ROOT_DIR, '.env'))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rappi_agent")

class RappiAgent:
    def __init__(self, headless=False):
        self.headless = headless
        self.cookies_file = os.path.join(ROOT_DIR, "data", "auth", "cookies_rappi.json")
        os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)

    async def _random_pause(self):
        await asyncio.sleep(random.uniform(3, 8))

    async def _load_cookies(self, context):
        if not os.path.exists(self.cookies_file):
            raise FileNotFoundError(f"No se encontró el archivo: {self.cookies_file}")
        with open(self.cookies_file, 'r') as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        logger.info(f"🍪 {len(cookies)} cookies cargadas.")

    async def search_medication(self, medication: str) -> Optional[Dict[str, Any]]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                channel="chrome",
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768}
            )
            await self._load_cookies(context)
            page = await context.new_page()

            try:
                # ── Navegar a home ──
                await page.goto("https://www.rappi.com.mx/", timeout=30000)
                await page.wait_for_load_state("networkidle")
                await self._random_pause()

                # ── Buscar ──
                search_input = await page.wait_for_selector(
                    "input[type='search'], input[placeholder*='Buscar']",
                    timeout=10000
                )
                if search_input is None:
                    raise Exception("No se encontró el campo de búsqueda.")
                await search_input.fill(medication)
                await search_input.press("Enter")
                await page.wait_for_load_state("networkidle")
                await self._random_pause()

                # ── Esperar resultados ──
                await page.wait_for_selector("div[data-qa='product-item']", timeout=15000)
                await self._random_pause()

                # ── Tiendas ──
                store_containers = await page.query_selector_all("div[data-testid^='search-result-cpgs-']")
                logger.info(f"📦 Encontradas {len(store_containers)} tiendas.")
                if not store_containers:
                    await page.screenshot(path="rappi_no_tiendas.png")
                    return None

                first_store = store_containers[0]

                # ── Nombre de la farmacia ──
                try:
                    farmacia_element = await first_store.query_selector("h2.chakra-text.css-cpodl")
                    farmacia = await farmacia_element.inner_text() if farmacia_element else "Farmacia en Rappi"
                    farmacia = farmacia.strip()
                except:
                    farmacia = "Farmacia en Rappi"

                # ── Producto ──
                product = await first_store.query_selector("div[data-qa='product-item']")
                if product is None:
                    await page.screenshot(path="rappi_no_producto.png")
                    return None

                # ── Precio ──
                try:
                    price_element = await product.query_selector("span[data-qa='product-price']")
                    price_text = await price_element.inner_text() if price_element else ""
                    precio = float(price_text.replace("$", "").replace(",", "").strip())
                except:
                    precio = None

                # ── Nombre del producto ──
                try:
                    name_element = await product.query_selector("h3[data-qa='product-name']")
                    nombre = await name_element.inner_text() if name_element else medication
                except:
                    nombre = medication

                # ── LINK DEL PRODUCTO (corregido) ──
                href = None

                # 1. Método principal: extraer ID de la imagen (UUID)
                try:
                    img = await product.query_selector("img")
                    if img:
                        src = await img.get_attribute("src")
                        if src:
                            # Buscar UUID en la URL de la imagen
                            match = re.search(r'/products/([a-f0-9-]+)\.', src)
                            if match:
                                product_id = match.group(1)
                                # Generar slug a partir del nombre
                                slug = nombre.lower().replace(' ', '-')
                                slug = re.sub(r'[^a-z0-9-]', '', slug)  # Eliminar caracteres especiales
                                href = f"https://www.rappi.com.mx/p/{slug}-{product_id}"
                                logger.info(f"✅ Link construido desde imagen: {href}")
                except Exception as e:
                    logger.warning(f"Error extrayendo de imagen: {e}")

                # 2. Si falla, buscar un enlace <a> que contenga '/p/'
                if not href:
                    try:
                        link_element = await product.query_selector("a[href*='/p/']")
                        if link_element:
                            href = await link_element.get_attribute("href")
                            logger.info(f"✅ Link encontrado en <a href>: {href}")
                    except Exception as e:
                        logger.warning(f"Error buscando <a href>: {e}")

                # 3. Último recurso: hacer clic en el producto y capturar URL
                if not href:
                    try:
                        logger.info("🖱️ Intentando obtener link mediante clic en el producto...")
                        # Hacer clic en el contenedor del producto
                        async with page.expect_navigation(timeout=15000) as nav_info:
                            await product.click()
                        href = page.url
                        if '/p/' in href:
                            logger.info(f"✅ Link obtenido por clic: {href}")
                            await page.go_back()
                            await page.wait_for_load_state("networkidle")
                            await self._random_pause()
                        else:
                            href = None
                    except Exception as e:
                        logger.warning(f"Error en clic: {e}")

                # ── FILTRO FINAL: descartar enlaces no válidos ──
                if href:
                    # Si contiene palabras clave de icono o no tiene '/p/', lo descartamos
                    if 'add-product' in href or 'icon' in href or '/p/' not in href:
                        logger.warning(f"⚠️ Enlace descartado (no válido): {href}")
                        href = None
                    # Completar URL si es relativa
                    elif not href.startswith("http"):
                        href = "https://www.rappi.com.mx" + href

                # ── Screenshot ──
                screenshot_bytes = await page.screenshot(full_page=False)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_dir = os.path.join(ROOT_DIR, "data", "screenshots", "rappi")
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, f"{medication.replace(' ', '_')}_{timestamp}.png")
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot_bytes)

                resultado = {
                    "medicamento": medication,
                    "farmacia": farmacia,
                    "precio": precio,
                    "precio_promo": None,
                    "link_producto": href,
                    "plataforma": "rappi",
                    "entrega_estimada": "25-35 min",
                    "fuente": "agente_rappi",
                    "fecha": datetime.now(timezone.utc).isoformat(),
                    "imagen_url": screenshot_path
                }

                # ── Guardar en BD ──
                if precio:
                    try:
                        save_precio({
                            "medicamento": medication.lower(),
                            "nombre_raw": nombre,
                            "farmacia": farmacia,
                            "precio": precio,
                            "url": href,
                            "imagen_url": screenshot_path,
                            "fuente": "agente_rappi",
                            "fecha": resultado["fecha"],
                        })
                        logger.info(f"💾 Guardado: {medication} - ${precio}")
                    except Exception as e:
                        logger.error(f"Error guardando en BD: {e}")

                await browser.close()
                return resultado

            except Exception as e:
                logger.error(f"❌ Error en búsqueda de {medication}: {e}", exc_info=True)
                try:
                    await page.screenshot(path=f"error_rappi_{medication.replace(' ', '_')}.png")
                except:
                    pass
                await browser.close()
                return None