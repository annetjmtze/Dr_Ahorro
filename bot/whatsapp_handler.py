import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

from llm.normalizer import MedicamentoNormalizer
from data.database import get_resumen, init_db, save_precio
from bot.counter import increment_and_check_limit, LIMITE_DIARIO, LIMITE_NOTIFICACION
from bot.telegram_notifier import send_telegram_message

load_dotenv()

# --------------------------------------------
#  INICIALIZAR BASE DE DATOS
# --------------------------------------------
init_db()  # Crea la tabla si no existe

# Poblar con datos de prueba SOLO si la tabla está vacía
def poblar_datos_prueba():
    """Inserta medicamentos de ejemplo si no hay registros."""
    from data.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM precios")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        logging.info("Poblando base de datos con datos de prueba...")
        ahora = datetime.now().isoformat()
        medicamentos = [
            {
                "medicamento": "paracetamol",
                "nombre_raw": "Paracetamol 500 mg",
                "farmacia": "Farmacia del Ahorro",
                "ciudad": "CDMX",
                "precio": 45.50,
                "precio_promo": 39.90,
                "vigencia": "2026-07-20",
                "fuente": "prueba_inicial",
                "fecha": ahora
            },
            {
                "medicamento": "paracetamol",
                "nombre_raw": "Paracetamol 500 mg",
                "farmacia": "Farmacia San Pablo",
                "ciudad": "CDMX",
                "precio": 48.00,
                "precio_promo": None,
                "vigencia": None,
                "fuente": "prueba_inicial",
                "fecha": ahora
            },
            {
                "medicamento": "ibuprofeno",
                "nombre_raw": "Ibuprofeno 400 mg",
                "farmacia": "Farmacias Similares",
                "ciudad": "CDMX",
                "precio": 89.00,
                "precio_promo": 79.50,
                "vigencia": "2026-07-25",
                "fuente": "prueba_inicial",
                "fecha": ahora
            },
            {
                "medicamento": "metformina",
                "nombre_raw": "Metformina 850 mg",
                "farmacia": "Farmacia del Ahorro",
                "ciudad": "CDMX",
                "precio": 120.00,
                "precio_promo": None,
                "vigencia": None,
                "fuente": "prueba_inicial",
                "fecha": ahora
            }
        ]
        for data in medicamentos:
            try:
                save_precio(data)
            except Exception as e:
                logging.error(f"Error insertando datos de prueba: {e}")
        logging.info("Base de datos poblada con datos de prueba.")

# Ejecutar la población de datos
poblar_datos_prueba()

# --------------------------------------------
#  APLICACIÓN FLASK
# --------------------------------------------
app = Flask(__name__)
normalizer = MedicamentoNormalizer()

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    resp = MessagingResponse()
    msg = resp.message()
    try:
        incoming_msg = request.form.get("Body", "").strip()
        sender = request.form.get("From", "desconocido")
        logging.info(f"Mensaje de {sender}: {incoming_msg}")

        if not incoming_msg:
            msg.body("Por favor, envía el nombre de un medicamento.")
            return Response(str(resp), mimetype="application/xml")

        if incoming_msg.lower().startswith("/medicamento"):
            incoming_msg = incoming_msg[len("/medicamento"):].strip()

        resultado = normalizer.normalizar(incoming_msg)
        if "error" in resultado:
            msg.body(f"❌ Error: {resultado['error']}")
            return Response(str(resp), mimetype="application/xml")

        nombre_generico = resultado.get('nombre_generico', '').lower()
        nombre_ingresado = resultado.get('nombre_ingresado', incoming_msg)

        # 1. Buscar con nombre genérico (lo que Claude devuelve)
        precios = get_resumen(nombre_generico)

        # 2. Si no hay, intentar con el nombre que el usuario escribió
        if not precios and nombre_ingresado:
            logging.info(f"Fallback: buscando con nombre ingresado: {nombre_ingresado}")
            precios = get_resumen(nombre_ingresado.lower())

        if precios:
            respuesta = f" *{nombre_generico.title()}*\n\n"
            respuesta += " *Precios en farmacias:*\n"
            for i, p in enumerate(precios, 1):
                linea = f"{i}. {p['farmacia']} — ${p['precio']:.2f}"
                if p.get('precio_promo'):
                    linea += f"\n ️ Promo: ${p['precio_promo']:.2f} (antes)"
                if p.get('vigencia'):
                    linea += f"\n Válido hasta: {p['vigencia']}"
                respuesta += linea + "\n"
            if precios and precios[0].get('fecha'):
                try:
                    ts = datetime.fromisoformat(precios[0]['fecha'])
                    delta = datetime.now() - ts
                    horas = int(delta.total_seconds() // 3600)
                    respuesta += f"\n Precios actualizados hace {horas} horas"
                except:
                    pass
            respuesta += "\n↩️ Escribe otro medicamento para comparar"
            msg.body(respuesta)
        else:
            # 3b. No hay precios → mensaje de fallback (Bug 1)
            msg.body(
                "Aún no tenemos precios para ese medicamento. "
                "Estamos actualizando nuestra base de datos — "
                "intenta de nuevo mañana o busca otro medicamento."
            )

        # --- NOTIFICACIÓN TELEGRAM (3c) ---
        if increment_and_check_limit():
            mensaje = (
                f"⚠️ *Dr. Ahorro* — Límite diario al 80%\n"
                f"Hoy se han procesado {LIMITE_NOTIFICACION} mensajes de {LIMITE_DIARIO} permitidos.\n"
                f"Revisa el uso del sandbox de Twilio."
            )
            send_telegram_message(mensaje)

    except Exception as e:
        logging.error(f"Error crítico en webhook: {e}", exc_info=True)
        msg.body("Ocurrió un error, intenta de nuevo.")

    return Response(str(resp), mimetype="application/xml")

# --------------------------------------------
#  FUNCIÓN PARA main.py
# --------------------------------------------
def run_whatsapp_bot(port=5000):
    """Arranca el servidor Flask para WhatsApp."""
    app.run(host="0.0.0.0", port=port, debug=False)

# --------------------------------------------
#  EJECUCIÓN DIRECTA
# --------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)