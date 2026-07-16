# save_rappi_cookies.py
import asyncio
import json
import os
from playwright.async_api import async_playwright

async def main():
    os.makedirs("data/auth", exist_ok=True)

    async with async_playwright() as p:
        # Usamos Chrome real (evita detección)
        browser = await p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768}
        )
        page = await context.new_page()

        # Ir a la página de login (sin esperar networkidle)
        await page.goto("https://www.rappi.com.mx/login", timeout=30000)
        await asyncio.sleep(3)  # esperar que cargue el DOM

        print("\n🔐 INICIA SESIÓN MANUALMENTE en el navegador que se abrió.")
        print("   - Correo: drahorro.agente@gmail.com")
        print("   - Cuando veas la página PRINCIPAL de Rappi (con tu nombre),")
        input("   - Presiona ENTER en esta terminal...\n")

        # Guardar cookies
        cookies = await context.cookies()
        with open("data/auth/cookies_rappi.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)

        print(f"✅ {len(cookies)} cookies guardadas en data/auth/cookies_rappi.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())