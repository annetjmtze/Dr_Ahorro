import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta, timezone
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

def formatear_respuesta(nombre_generico: str, farmacias: list, delivery: list) -> str:
    """
    Construye el mensaje en el formato exacto requerido para la Semana 3.
    """
    lines = []
    lines.append(f"💊 *{nombre_generico.title()}*")
    lines.append("")

    # ---- 1. FARMACIAS FÍSICAS ----
    if farmacias:
        lines.append("📍 *Farmacias cercanas:*")
        for i, p in enumerate(farmacias, 1):
            precio = p['precio']
            farmacia = p['farmacia']
            linea = f"{i}. {farmacia} — ${precio:.2f}"
            if p.get('precio_promo'):
                linea += f"\n   🏷️ Promo: 2x1 hasta el {p.get('vigencia', 'próximo aviso')}"
            if p.get('vigencia') and not p.get('precio_promo'):
                linea += f"\n   🏷️ Válido hasta: {p['vigencia']}"
            lines.append(linea)
        lines.append("")
    else:
        lines.append("📍 No hay farmacias físicas con precios recientes.\n")

    # ---- 2. DELIVERY ----
    if delivery:
        lines.append("🛵 *También disponible a domicilio:*")
        for p in delivery:
            # Determinar plataforma
            fuente = p['fuente'].lower()
            if 'rappi' in fuente:
                plataforma = "Rappi"
            elif 'ubereats' in fuente:
                plataforma = "Uber Eats"
            else:
                plataforma = "Delivery"

            # Link: priorizar el de la BD, si no, generar búsqueda
            url = p.get('url') or p.get('link_producto')
            if not url:
                busqueda = nombre_generico.replace(' ', '+')
                if 'rappi' in fuente:
                    url = f"https://rappi.com.mx/search?q={busqueda}"
                elif 'ubereats' in fuente:
                    url = f"https://ubereats.com/mx/search?q={busqueda}"
                else:
                    url = "#"

            # Tiempo de entrega (si no existe, usar default)
            entrega = p.get('entrega_estimada', '25-35 min')

            linea = f"• {plataforma} ({p['farmacia']}) — ${p['precio']:.2f}"
            linea += f"\n  ⏱️ {entrega} · 🔗 Pedir aquí: {url}"
            lines.append(linea)
        lines.append("")

    # ---- 3. PIE DE PÁGINA: actualización ----
    if farmacias or delivery:
        # Tomar la fecha más reciente de todos los precios
        todos = farmacias + delivery
        fechas = [p.get('fecha') for p in todos if p.get('fecha')]
        if fechas:
            try:
                # Tomar la fecha más reciente
                ultima = max(fechas)
                if isinstance(ultima, str):
                    ultima = datetime.fromisoformat(ultima.replace('Z', '+00:00'))
                ahora = datetime.now(timezone.utc)
                delta = ahora - ultima
                if delta.total_seconds() < 3600:
                    tiempo = "hace menos de 1 hora"
                elif delta.total_seconds() < 7200:
                    tiempo = "hace 1 hora"
                elif delta.total_seconds() < 86400:
                    horas = int(delta.total_seconds() // 3600)
                    tiempo = f"hace {horas} horas"
                else:
                    dias = int(delta.total_seconds() // 86400)
                    tiempo = f"hace {dias} días"
                lines.append(f"📅 Precios actualizados {tiempo}")
            except:
                pass

    lines.append("\n↩️ Escribe otro medicamento para comparar")
    return "\n".join(lines)

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

        # Normalizar (usando Claude)
        resultado = normalizer.normalizar(incoming_msg)
        if "error" in resultado:
            msg.body(f"❌ Error: {resultado['error']}")
            return Response(str(resp), mimetype="application/xml")

        nombre_generico = resultado.get('nombre_generico', '').lower()
        nombre_ingresado = resultado.get('nombre_ingresado', incoming_msg).lower()

        # ---- BUSCAR PRECIOS CON AMBOS NOMBRES ----
        # 1. Buscar con nombre genérico (ej: acetaminofeno)
        precios = get_resumen(nombre_generico)
        # 2. Buscar con el nombre que el usuario escribió (ej: paracetamol)
        precios_original = get_resumen(nombre_ingresado)

        # Combinar ambas listas evitando duplicados (clave: farmacia+precio+url)
        combined = []
        seen = set()
        for p in precios + precios_original:
            key = (p.get('farmacia'), p.get('precio'), p.get('url'))
            if key not in seen:
                seen.add(key)
                combined.append(p)

        precios = combined

        # ---- SI HAY PRECIOS RECIENTES ----
        if precios:
            farmacias = []
            delivery = []
            for p in precios:
                fuente = p.get('fuente', '').lower()
                if fuente in ['rappi', 'ubereats', 'delivery', 'agente_rappi', 'agente_ubereats']:
                    delivery.append(p)
                else:
                    farmacias.append(p)

            # Ordenar por precio (menor a mayor)
            farmacias.sort(key=lambda x: x['precio'])
            delivery.sort(key=lambda x: x['precio'])

            # Construir respuesta con el formato requerido
            respuesta = formatear_respuesta(nombre_generico, farmacias, delivery)
            msg.body(respuesta)

        else:
            # ---- SIN PRECIOS RECIENTES: BUSCAR HISTÓRICOS ----
            historicos = get_last_precios(nombre_generico, limit=5)
            if not historicos and nombre_ingresado:
                historicos = get_last_precios(nombre_ingresado, limit=5)

            if historicos:
                respuesta = f"⚠️ *No hay precios actualizados en las últimas 24 horas.*\n"
                respuesta += f"Mostrando los últimos *{len(historicos)}* registros disponibles:\n\n"
                for i, p in enumerate(historicos, 1):
                    linea = f"{i}. {p['farmacia']} — ${p['precio']:.2f}"
                    if p.get('precio_promo'):
                        linea += f"\n ️ Promo: ${p['precio_promo']:.2f} (antes)"
                    if p.get('vigencia'):
                        linea += f"\n Válido hasta: {p['vigencia']}"
                    respuesta += linea + "\n"
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
                # ---- FALBACK RÁPIDO (menos de 5 segundos) ----
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
        if "429" in str(e) or "Too Many Requests" in str(e):
            msg.body("Alcanzamos el límite de consultas por hoy. Vuelve mañana.")
        else:
            msg.body("Ocurrió un error, intenta de nuevo.")

    return Response(str(resp), mimetype="application/xml")

# --------------------------------------------
#  FUNCIÓN PARA main.py
# --------------------------------------------
def run_whatsapp_bot(port=5000):
    app.run(host="0.0.0.0", port=port, debug=False)

# --------------------------------------------
#  EJECUCIÓN DIRECTA
# --------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)