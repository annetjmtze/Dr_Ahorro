import os
import sys
import logging
import requests
from datetime import datetime

# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.database import get_connection
from dotenv import load_dotenv
load_dotenv()

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # 8801980649

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generar_reporte():
    """Genera el reporte diario y lo envía por Telegram."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Detectar si es SQLite o PostgreSQL
        es_sqlite = 'sqlite' in str(conn)
        if es_sqlite:
            date_func = "DATE(timestamp)"
            round_func = "ROUND(AVG(ahorro_vs_delivery), 2)"
        else:
            date_func = "DATE(timestamp)"
            round_func = "ROUND(AVG(ahorro_vs_delivery)::numeric, 2)"

        # 1. Medicamentos más buscados hoy
        cursor.execute(f"""
            SELECT medicamento, COUNT(*) busquedas
            FROM analisis_busquedas
            WHERE {date_func} = CURRENT_DATE
            GROUP BY medicamento
            ORDER BY busquedas DESC
            LIMIT 5;
        """)
        top_meds = cursor.fetchall()

        # 2. Ahorro promedio
        cursor.execute(f"""
            SELECT {round_func}
            FROM analisis_busquedas
            WHERE {date_func} = CURRENT_DATE
              AND ahorro_vs_delivery IS NOT NULL;
        """)
        ahorro_avg = cursor.fetchone()[0]

        # 3. Usuarios activos
        cursor.execute(f"""
            SELECT COUNT(DISTINCT usuario)
            FROM analisis_busquedas
            WHERE {date_func} = CURRENT_DATE;
        """)
        usuarios_activos = cursor.fetchone()[0]

        # 4. Consultas urgentes
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM analisis_busquedas
            WHERE {date_func} = CURRENT_DATE
              AND urgente = 1;
        """)
        consultas_urgentes = cursor.fetchone()[0]

        # Construir mensaje
        if not top_meds and ahorro_avg is None and usuarios_activos == 0:
            mensaje = "📊 Sin actividad hoy"
        else:
            lines = [f"📊 *Reporte diario - {datetime.now().strftime('%d/%m/%Y')}*", ""]
            if top_meds:
                lines.append("🏥 *Medicamentos más buscados:*")
                for med, count in top_meds:
                    lines.append(f"  • {med}: {count} búsquedas")
                lines.append("")
            if ahorro_avg is not None:
                lines.append(f"💰 *Ahorro promedio por consulta:* ${ahorro_avg:.2f}")
                lines.append("")
            if usuarios_activos:
                lines.append(f"👥 *Usuarios activos:* {usuarios_activos}")
                lines.append("")
            if consultas_urgentes:
                lines.append(f"⚡ *Consultas urgentes:* {consultas_urgentes}")
                lines.append("")
            lines.append("📌 *Nota:* Los datos de zona y diferencia Rappi vs física aún no se registran.")
            mensaje = "\n".join(lines)

        # Enviar por Telegram
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": mensaje,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("✅ Reporte enviado correctamente")
        else:
            logger.warning("⚠️ Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID, no se envió el reporte")

    except Exception as e:
        logger.error(f"❌ Error generando/enviando reporte: {e}", exc_info=True)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    generar_reporte()