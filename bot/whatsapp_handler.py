import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

from llm.normalizer import MedicamentoNormalizer
from data.database import get_resumen, init_db, save_precio, get_last_precios
from bot.counter import increment_and_check_limit, is_limit_reached, LIMITE_DIARIO, LIMITE_NOTIFICACION
from bot.telegram_notifier import send_telegram_message

load_dotenv()

# --------------------------------------------
#  INICIALIZAR BASE DE DATOS
# --------------------------------------------
init_db()  # Crea la tabla si no existe

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

        # ---------- VERIFICAR LÍMITE DIARIO ----------
        if is_limit_reached():
            msg.body("Alcanzamos el límite de consultas por hoy. Vuelve mañana.")
            logging.warning(f"Límite diario alcanzado, rechazando mensaje de {sender}")
            return Response(str(resp), mimetype="application/xml")
        # --------------------------------------------

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

        # 1. Buscar con nombre genérico (lo que Claude devuelve) - solo últimas 24h
        precios = get_resumen(nombre_generico)

        # 2. Si no hay, intentar con el nombre que el usuario escribió - últimas 24h
        if not precios and nombre_ingresado:
            logging.info(f"Fallback: buscando con nombre ingresado: {nombre_ingresado}")
            precios = get_resumen(nombre_ingresado.lower())

        if precios:
            # ---- Construir respuesta con precios recientes ----
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
            # ---- Sin precios recientes: buscar históricos ----
            historicos = get_last_precios(nombre_generico, limit=5)
            if not historicos and nombre_ingresado:
                historicos = get_last_precios(nombre_ingresado.lower(), limit=5)

            if historicos:
                # Mostrar últimos registros disponibles (aunque no sean recientes)
                respuesta = f"⚠️ *No hay precios actualizados en las últimas 24 horas.*\n"
                respuesta += f"Mostrando los últimos *{len(historicos)}* registros disponibles:\n\n"
                for i, p in enumerate(historicos, 1):
                    linea = f"{i}. {p['farmacia']} — ${p['precio']:.2f}"
                    if p.get('precio_promo'):
                        linea += f"\n ️ Promo: ${p['precio_promo']:.2f} (antes)"
                    if p.get('vigencia'):
                        linea += f"\n Válido hasta: {p['vigencia']}"
                    respuesta += linea + "\n"
                # Mostrar cuándo fue la última actualización
                if historicos and historicos[0].get('fecha'):
                    try:
                        ts = datetime.fromisoformat(historicos[0]['fecha'])
                        delta = datetime.now() - ts
                        horas = int(delta.total_seconds() // 3600)
                        respuesta += f"\n Última actualización hace {horas} horas"
                    except:
                        pass
                respuesta += "\n↩️ Escribe otro medicamento para comparar"
                msg.body(respuesta)
            else:
                # ---- No hay ningún registro en la base de datos ----
                ficha = f"📋 *Ficha de {nombre_ingresado.title()}*\n\n"
                ficha += f"*Nombre genérico:* {resultado.get('nombre_generico', 'No disponible')}\n"
                ficha += f"*Uso principal:* {resultado.get('uso_principal', 'No disponible')}\n"
                receta = "Sí" if resultado.get('requiere_receta') else "No"
                ficha += f"*¿Requiere receta?* {receta}\n"
                ficha += "\n⚠️ Aún no tenemos precios para este medicamento. Estamos actualizando nuestra base de datos — intenta de nuevo mañana o busca otro medicamento."
                msg.body(ficha)

        # --- NOTIFICACIÓN TELEGRAM (80%) ---
        if increment_and_check_limit():
            mensaje = (
                f"⚠️ *Dr. Ahorro* — Límite diario al 80%\n"
                f"Hoy se han procesado {LIMITE_NOTIFICACION} mensajes de {LIMITE_DIARIO} permitidos.\n"
                f"Revisa el uso del sandbox de Twilio."
            )
            send_telegram_message(mensaje)

    except Exception as e:
        logging.error(f"Error crítico en webhook: {e}", exc_info=True)
        # Si es error de rate limit de Twilio, mensaje específico
        if "429" in str(e) or "Too Many Requests" in str(e):
            msg.body("Alcanzamos el límite de consultas por hoy. Vuelve mañana.")
        else:
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