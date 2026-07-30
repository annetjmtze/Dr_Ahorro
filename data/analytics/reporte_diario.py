import os
import sys
import logging
import requests
from datetime import datetime, date

# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.database import get_connection, IS_PROD
from dotenv import load_dotenv
load_dotenv()

# Variables de entorno
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Ej: 8801980649

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generar_reporte():
    """Genera el reporte diario y lo envía por Telegram (o lo imprime en consola)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hoy = date.today().isoformat()

        # 1. Medicamentos más buscados hoy
        if IS_PROD:
            cursor.execute("""
                SELECT medicamento, COUNT(*) busquedas
                FROM analisis_busquedas
                WHERE DATE(fecha) = %s
                GROUP BY medicamento
                ORDER BY busquedas DESC
                LIMIT 5
            """, (hoy,))
        else:
            cursor.execute("""
                SELECT medicamento, COUNT(*) busquedas
                FROM analisis_busquedas
                WHERE DATE(fecha) = ?
                GROUP BY medicamento
                ORDER BY busquedas DESC
                LIMIT 5
            """, (hoy,))
        top_meds = cursor.fetchall()

        # 2. Ahorro promedio
        if IS_PROD:
            cursor.execute("""
                SELECT ROUND(AVG(ahorro_calculado)::numeric, 2)
                FROM analisis_busquedas
                WHERE DATE(fecha) = %s AND ahorro_calculado IS NOT NULL
            """, (hoy,))
        else:
            cursor.execute("""
                SELECT ROUND(AVG(ahorro_calculado), 2)
                FROM analisis_busquedas
                WHERE DATE(fecha) = ? AND ahorro_calculado IS NOT NULL
            """, (hoy,))
        ahorro_row = cursor.fetchone()
        ahorro_avg = ahorro_row[0] if ahorro_row else None

        # 3. Usuarios activos
        if IS_PROD:
            cursor.execute("""
                SELECT COUNT(DISTINCT usuario)
                FROM analisis_busquedas
                WHERE DATE(fecha) = %s
            """, (hoy,))
        else:
            cursor.execute("""
                SELECT COUNT(DISTINCT usuario)
                FROM analisis_busquedas
                WHERE DATE(fecha) = ?
            """, (hoy,))
        usuarios_activos = cursor.fetchone()[0] or 0

        # 4. Consultas urgentes
        if IS_PROD:
            cursor.execute("""
                SELECT COUNT(*)
                FROM analisis_busquedas
                WHERE DATE(fecha) = %s AND urgente = TRUE
            """, (hoy,))
        else:
            cursor.execute("""
                SELECT COUNT(*)
                FROM analisis_busquedas
                WHERE DATE(fecha) = ? AND urgente = 1
            """, (hoy,))
        consultas_urgentes = cursor.fetchone()[0] or 0

        # 5. Diferencia Rappi vs Física (por medicamento)
        if IS_PROD:
            cursor.execute("""
                SELECT medicamento,
                       ROUND(AVG(precio_rappi - precio_fisica)::numeric, 2) diferencia
                FROM analisis_busquedas
                WHERE DATE(fecha) = %s
                  AND precio_rappi IS NOT NULL
                  AND precio_fisica IS NOT NULL
                GROUP BY medicamento
                ORDER BY diferencia DESC
                LIMIT 5
            """, (hoy,))
        else:
            cursor.execute("""
                SELECT medicamento,
                       ROUND(AVG(precio_rappi - precio_fisica), 2) diferencia
                FROM analisis_busquedas
                WHERE DATE(fecha) = ?
                  AND precio_rappi IS NOT NULL
                  AND precio_fisica IS NOT NULL
                GROUP BY medicamento
                ORDER BY diferencia DESC
                LIMIT 5
            """, (hoy,))
        diff_meds = cursor.fetchall()

        # 6. Zona más activa
        if IS_PROD:
            cursor.execute("""
                SELECT zona, COUNT(*) consultas
                FROM analisis_busquedas
                WHERE DATE(fecha) = %s AND zona IS NOT NULL
                GROUP BY zona
                ORDER BY consultas DESC
                LIMIT 1
            """, (hoy,))
        else:
            cursor.execute("""
                SELECT zona, COUNT(*) consultas
                FROM analisis_busquedas
                WHERE DATE(fecha) = ? AND zona IS NOT NULL
                GROUP BY zona
                ORDER BY consultas DESC
                LIMIT 1
            """, (hoy,))
        zona_row = cursor.fetchone()

        # --- Construir mensaje ---
        if not top_meds and ahorro_avg is None and usuarios_activos == 0:
            mensaje = f"📊 *Reporte Diario - {date.today().strftime('%d/%m/%Y')}*\n\nSin actividad hoy."
        else:
            lines = [f"📊 *Reporte Diario - {date.today().strftime('%d/%m/%Y')}*", ""]
            
            if top_meds:
                lines.append("💊 *Medicamentos más buscados:*")
                for med, count in top_meds:
                    lines.append(f"  • {med}: {count} búsquedas")
                lines.append("")
            
            if ahorro_avg is not None:
                lines.append(f"💰 *Ahorro promedio por consulta:* ${ahorro_avg:.2f}")
                lines.append("")
            
            lines.append(f"👥 *Usuarios activos:* {usuarios_activos}")
            lines.append("")
            
            if consultas_urgentes:
                lines.append(f"🚨 *Consultas urgentes:* {consultas_urgentes}")
                lines.append("")
            
            if diff_meds:
                lines.append("📈 *Diferencia Rappi vs Física (más caro):*")
                for med, diff in diff_meds:
                    lines.append(f"  • {med}: +${diff:.2f}")
                lines.append("")
            else:
                lines.append("📈 *Diferencia Rappi vs Física:* Sin datos suficientes.")
                lines.append("")
            
            if zona_row:
                zona, consultas = zona_row
                lines.append(f"📍 *Zona más activa:* {zona} ({consultas} consultas)")
            else:
                lines.append("📍 *Zona más activa:* Sin datos.")
            
            mensaje = "\n".join(lines)

        # --- Enviar por Telegram (si está configurado) ---
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": mensaje,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("✅ Reporte enviado correctamente a Telegram")
        else:
            # Si no hay token, imprimimos en consola para pruebas
            print("\n" + "="*60)
            print(mensaje)
            print("="*60 + "\n")
            logger.warning("⚠️ Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID, reporte impreso en consola.")

    except Exception as e:
        logger.error(f"❌ Error generando/enviando reporte: {e}", exc_info=True)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    generar_reporte()