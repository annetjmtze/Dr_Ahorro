import os
import sys
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# ── Configurar path ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Importar agentes ──
try:
    from data.agents.playwright_agent import main as playwright_main
    from data.agents.rappi_agent import RappiAgent
    from data.agents.ubereats_agent import UberEatsAgent
except ImportError as e:
    print(f"Error importando agentes: {e}")
    sys.exit(1)

from data.database import init_db, get_connection, contar_por_fuente, count_precios

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================
# FUNCIONES ASÍNCRONAS PARA CADA AGENTE
# ============================================================

async def ejecutar_agentes_delivery():
    """Ejecuta los agentes de Rappi y Uber Eats para medicamentos clave."""
    medicamentos = [
        "paracetamol 500mg",
        "ibuprofeno 400mg",
        "omeprazol 20mg",
        "naproxeno 500mg"
    ]
    
    rappi = RappiAgent(headless=True)
    ubereats = UberEatsAgent(headless=True)
    
    for med in medicamentos:
        logger.info(f"🔍 Buscando {med} en Rappi...")
        try:
            await rappi.search_medication(med)
            logger.info(f"✅ Rappi completado para {med}")
        except Exception as e:
            logger.error(f"❌ Error en Rappi para {med}: {e}", exc_info=True)
        
        logger.info(f"🔍 Buscando {med} en Uber Eats...")
        try:
            await ubereats.search_medication(med)
            logger.info(f"✅ Uber Eats completado para {med}")
        except Exception as e:
            logger.error(f"❌ Error en Uber Eats para {med}: {e}", exc_info=True)

async def ejecutar_agentes_playwright():
    """Ejecuta los agentes Playwright (farmacias físicas) para medicamentos clave."""
    medicamentos = [
        "paracetamol",
        "ibuprofeno",
        "omeprazol",
        "naproxeno",
        "metformina",
        "losartan"
    ]
    
    for med in medicamentos:
        logger.info(f"🎭 Ejecutando Playwright para {med}...")
        try:
            await playwright_main(med)
            logger.info(f"✅ Playwright completado para {med}")
        except Exception as e:
            logger.error(f"❌ Error en Playwright para {med}: {e}", exc_info=True)

# ============================================================
# PIPELINE COMPLETO (se ejecuta cada 6 horas)
# ============================================================

def pipeline_completo():
    """Ejecuta todos los agentes secuencialmente."""
    logger.info("=" * 60)
    logger.info(f"🚀 INICIANDO PIPELINE COMPLETO - {datetime.now()}")
    logger.info("=" * 60)
    
    # 1. Web Scraper (si existe)
    try:
        from scrapers.web_scraper import main as scraper_main
        logger.info("🕷️ Ejecutando web scraper...")
        scraper_main()
        logger.info("✅ Web scraper finalizado")
    except ImportError:
        logger.info("ℹ️ Web scraper no disponible, continuando...")
    except Exception as e:
        logger.error(f"❌ Error en web scraper: {e}", exc_info=True)
    
    # 2. Agentes Playwright (farmacias físicas)
    try:
        logger.info("🎭 Ejecutando agentes Playwright...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(ejecutar_agentes_playwright())
        loop.close()
        logger.info("✅ Agentes Playwright finalizados")
    except Exception as e:
        logger.error(f"❌ Error en agentes Playwright: {e}", exc_info=True)
    
    # 3. Agentes de Delivery (Rappi + Uber Eats)
    try:
        logger.info("🛵 Ejecutando agentes de delivery...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(ejecutar_agentes_delivery())
        loop.close()
        logger.info("✅ Agentes de delivery finalizados")
    except Exception as e:
        logger.error(f"❌ Error en agentes de delivery: {e}", exc_info=True)
    
    # 4. Resumen de la ejecución
    try:
        total = count_precios()
        fuente_counts = contar_por_fuente()
        logger.info("📊 Resumen de la base de datos:")
        logger.info(f"   Total de registros: {total}")
        for fuente, count in fuente_counts.items():
            logger.info(f"   {fuente}: {count} registros")
    except Exception as e:
        logger.error(f"❌ Error obteniendo resumen: {e}", exc_info=True)
    
    logger.info("=" * 60)
    logger.info(f"✅ PIPELINE COMPLETADO - {datetime.now()}")
    logger.info("=" * 60)

# ============================================================
# MAIN - INICIAR SCHEDULER
# ============================================================

if __name__ == "__main__":
    # Inicializar base de datos
    init_db()
    logger.info("🗄️ Base de datos inicializada")
    
    # Verificar conexión
    try:
        conn = get_connection()
        conn.close()
        logger.info("✅ Conexión a base de datos exitosa")
    except Exception as e:
        logger.error(f"❌ Error conectando a base de datos: {e}")
        sys.exit(1)
    
    # Ejecutar pipeline una vez al inicio
    logger.info("🔄 Ejecutando pipeline inicial...")
    pipeline_completo()
    
    # Crear scheduler
    scheduler = BlockingScheduler()
    
    # Programar pipeline cada 6 horas
    scheduler.add_job(
        pipeline_completo,
        'interval',
        hours=6,
        id='pipeline_6h',
        next_run_time=datetime.now()  # se ejecutará ahora mismo (ya lo hicimos, pero si no, lo haría)
    )
    logger.info("⏰ Pipeline programado cada 6 horas")
    
    try:
        logger.info("🚀 Scheduler iniciado. Presiona Ctrl+C para detener.")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("⏹️ Scheduler detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en scheduler: {e}", exc_info=True)
        sys.exit(1)