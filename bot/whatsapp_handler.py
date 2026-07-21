import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta, timezone
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

from llm.normalizer import MedicamentoNormalizer
from data.database import (
    get_resumen, init_db, save_precio, get_last_precios,
    validar_coherencia_producto, validar_precio, normalizar_farmacia,
    get_connection, get_precios
)
from bot.counter import increment_and_check_limit, is_limit_reached, LIMITE_DIARIO, LIMITE_NOTIFICACION
from bot.telegram_notifier import send_telegram_message

load_dotenv()

# --------------------------------------------
#  INICIALIZAR BASE DE DATOS
# --------------------------------------------
init_db()

# --------------------------------------------
#  APLICACIÓN FLASK
# --------------------------------------------
app = Flask(__name__)
normalizer = MedicamentoNormalizer()

# Configurar logging para ver detalles
logging.basicConfig(level=logging.INFO)

def formatear_respuesta(nombre_generico: str, farmacias: list, delivery: list) -> str:
    lines = []
    lines.append(f"💊 *{nombre_generico.title()}*")
    lines.append("")

    if farmacias:
        lines.append("📍 *Farmacias cercanas:*")
        for i, p in enumerate(farmacias[:10], 1):
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

    if delivery:
        lines.append("🛵 *También disponible a domicilio:*")
        for p in delivery[:3]:
            fuente = p['fuente'].lower()
            if 'rappi' in fuente:
                plataforma = "Rappi"
                base_url = "https://www.rappi.com.mx"
            elif 'ubereats' in fuente:
                plataforma = "Uber Eats"
                base_url = "https://ubereats.com/mx"
            else:
                plataforma = "Delivery"
                base_url = "#"

            # Obtener URL de la BD
            url = p.get('url') or p.get('link_producto')
            # Si el url es inválido (contiene "add-product-icon" o está vacío), construir búsqueda
            if not url or 'add-product-icon' in url:
                busqueda = nombre_generico.replace(' ', '+')
                if 'rappi' in fuente:
                    url = f"{base_url}/search?q={busqueda}"
                elif 'ubereats' in fuente:
                    url = f"{base_url}/search?q={busqueda}"
                else:
                    url = "#"

            entrega = p.get('entrega_estimada', '25-35 min')
            linea = f"• {plataforma} ({p['farmacia']}) — ${p['precio']:.2f}"
            linea += f"\n  ⏱️ {entrega} · 🔗 Pedir aquí: {url}"
            lines.append(linea)
        lines.append("")

    if farmacias or delivery:
        todos = farmacias + delivery
        fechas = [p.get('fecha') for p in todos if p.get('fecha')]
        if fechas:
            try:
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

        if is_limit_reached():
            msg.body("Alcanzamos el límite de consultas por hoy. Vuelve mañana.")
            logging.warning(f"Límite diario alcanzado, rechazando mensaje de {sender}")
            return Response(str(resp), mimetype="application/xml")

        if not incoming_msg:
            msg.body("Por favor, envía el nombre de un medicamento.")
            return Response(str(resp), mimetype="application/xml")

        resultado = normalizer.normalizar(incoming_msg)
        if "error" in resultado:
            msg.body(f"❌ Error: {resultado['error']}")
            return Response(str(resp), mimetype="application/xml")

        nombre_generico = resultado.get('nombre_generico', '').lower()
        nombre_ingresado = resultado.get('nombre_ingresado', incoming_msg).lower()
        medicamento_ref = nombre_generico if nombre_generico else nombre_ingresado

        # ---- OBTENER PRECIOS RECIENTES (últimas 24h) ----
        precios_recientes = get_resumen(nombre_generico) + get_resumen(nombre_ingresado)
        logging.info(f"Registros recientes obtenidos: {len(precios_recientes)}")

        # ---- SI NO HAY RECIENTES, BUSCAR HISTÓRICOS (sin límite de tiempo) ----
        if not precios_recientes:
            logging.info("No hay registros recientes, buscando históricos...")
            historicos_todos = get_last_precios(nombre_generico, limit=20) + get_last_precios(nombre_ingresado, limit=20)
            # Eliminar duplicados por combinación de campos
            seen = set()
            precios_recientes = []
            for p in historicos_todos:
                key = (p.get('farmacia'), p.get('precio'), p.get('nombre_raw'))
                if key not in seen:
                    seen.add(key)
                    precios_recientes.append(p)
            logging.info(f"Registros históricos obtenidos: {len(precios_recientes)}")

        # ---- APLICAR FILTROS DE COHERENCIA, PRECIO Y DEDUPLICACIÓN ----
        conn = get_connection()
        try:
            # Filtro coherencia
            filtrados_coherencia = []
            for p in precios_recientes:
                if validar_coherencia_producto(p.get('nombre_raw', ''), medicamento_ref):
                    filtrados_coherencia.append(p)
                else:
                    logging.info(f"Descartado por incoherencia: {p.get('nombre_raw', '')[:40]} vs {medicamento_ref}")

            logging.info(f"Después de filtro de coherencia: {len(filtrados_coherencia)}")

            # Filtro precio
            filtrados_precio = []
            for p in filtrados_coherencia:
                if validar_precio(p['precio'], medicamento_ref, conn):
                    filtrados_precio.append(p)
                else:
                    logging.info(f"Descartado por precio anómalo: ${p['precio']} para {medicamento_ref}")

            logging.info(f"Después de filtro de precio: {len(filtrados_precio)}")

            # Deduplicación por farmacia (mantener el más reciente) con normalización a minúsculas
            mejores = {}
            for p in filtrados_precio:
                farmacia_norm = normalizar_farmacia(p['farmacia']).lower()
                if farmacia_norm not in mejores or p['fecha'] > mejores[farmacia_norm]['fecha']:
                    mejores[farmacia_norm] = p
            precios_depurados = list(mejores.values())
            logging.info(f"Después de deduplicación: {len(precios_depurados)}")
        finally:
            conn.close()

        # ---- SEPARAR FÍSICAS Y DELIVERY ----
        delivery = [p for p in precios_depurados if p.get('fuente', '').lower() in ['agente_rappi', 'agente_ubereats']]
        farmacias = [p for p in precios_depurados if p.get('fuente', '').lower() not in ['agente_rappi', 'agente_ubereats']]

        # Ordenar
        farmacias.sort(key=lambda x: x['precio'])
        delivery.sort(key=lambda x: x['precio'])

        if farmacias or delivery:
            respuesta = formatear_respuesta(nombre_generico, farmacias, delivery)
            msg.body(respuesta)
        else:
            # Si no hay precios después de los filtros, mostrar la ficha de información
            ficha = f"📋 *Ficha de {nombre_ingresado.title()}*\n\n"
            ficha += f"*Nombre genérico:* {resultado.get('nombre_generico', 'No disponible')}\n"
            ficha += f"*Uso principal:* {resultado.get('uso_principal', 'No disponible')}\n"
            receta = "Sí" if resultado.get('requiere_receta') else "No"
            ficha += f"*¿Requiere receta?* {receta}\n"
            ficha += "\n⚠️ Aún no tenemos precios para este medicamento. Estamos actualizando nuestra base de datos — intenta de nuevo mañana o busca otro medicamento."
            msg.body(ficha)

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

def run_whatsapp_bot(port=5000):
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)