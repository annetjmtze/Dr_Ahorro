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
#  DETECCIÓN DE ENTORNO
# --------------------------------------------
IS_PROD = os.getenv("DATABASE_URL") is not None

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

# Diccionario para guardar el contexto de la última búsqueda de cada usuario
user_context = {}
CONTEXTO_EXPIRACION = timedelta(minutes=30)

# ------------------------------------------------------------
#  FUNCIONES AUXILIARES
# ------------------------------------------------------------

def obtener_principio_activo_mejorado(resultado, nombre_generico, nombre_ingresado):
    """
    Devuelve el principio activo más adecuado para la búsqueda.
    """
    # Si el normalizador ya dio un principio activo, lo usamos
    if resultado.get('principio_activo'):
        return resultado['principio_activo']
    
    # Casos especiales (mapeo manual)
    nombre_lower = nombre_ingresado.lower()
    if 'clavulánico' in nombre_lower or 'clavulanico' in nombre_lower:
        return 'amoxicilina'
    if 'aspirina' in nombre_lower:
        return 'aspirina'
    if 'ibuprofeno' in nombre_lower:
        return 'ibuprofeno'
    if 'paracetamol' in nombre_lower:
        return 'paracetamol'
    
    # Fallback: usar nombre_generico
    return nombre_generico

def get_alternativas(principio_activo: str, limit: int = 5):
    """
    Busca medicamentos que contengan el principio activo en la columna 'medicamento'
    y que tengan precio registrado. Retorna lista de dicts.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if IS_PROD:
            cursor.execute("""
                SELECT medicamento, farmacia, precio, fecha, fuente, url
                FROM precios
                WHERE (LOWER(medicamento) LIKE LOWER(%s) OR LOWER(nombre_raw) LIKE LOWER(%s))
                  AND precio IS NOT NULL
                  AND precio > 0
                ORDER BY fecha DESC, precio ASC
                LIMIT %s
            """, (f'%{principio_activo}%', f'%{principio_activo}%', limit))
        else:
            cursor.execute("""
                SELECT medicamento, farmacia, precio, fecha, fuente, url
                FROM precios
                WHERE (LOWER(medicamento) LIKE LOWER(?) OR LOWER(nombre_raw) LIKE LOWER(?))
                  AND precio IS NOT NULL
                  AND precio > 0
                ORDER BY fecha DESC, precio ASC
                LIMIT ?
            """, (f'%{principio_activo}%', f'%{principio_activo}%', limit))
        rows = cursor.fetchall()
    except Exception as e:
        logging.error(f"Error en get_alternativas: {e}")
        rows = []
    finally:
        conn.close()

    resultados = []
    for row in rows:
        if IS_PROD:
            # row es dict
            resultados.append({
                'nombre': row['medicamento'],
                'presentacion': '',
                'farmacia': row['farmacia'],
                'precio': row['precio'],
                'fecha': row['fecha'],
                'fuente': row['fuente'] or 'farmacia',
                'url': row['url'] or ''
            })
        else:
            # row es tuple (SQLite)
            resultados.append({
                'nombre': row[0],
                'presentacion': '',
                'farmacia': row[1],
                'precio': row[2],
                'fecha': row[3],
                'fuente': row[4] or 'farmacia',
                'url': row[5] or ''
            })
    return resultados

def construir_mensaje_fallback(nombre_ingresado, nombre_generico, requiere_receta, alternativas, principio_activo):
    mensaje = ""
    
    # 1. Aviso de receta (si aplica) - SIEMPRE PRIMERO
    if requiere_receta:
        mensaje += "⚠️ *Este medicamento requiere receta médica*\n\n"
    
    # 2. Encabezado del medicamento buscado
    mensaje += f"💊 *{nombre_ingresado.title()}*\n"
    
    # 3. Mensaje de que no hay precios
    mensaje += "Aún no tenemos precios en tu zona,\n"
    mensaje += "pero encontramos estos similares:\n\n"
    
    # 4. Listar alternativas
    if alternativas:
        for alt in alternativas[:5]:
            mensaje += f"• {alt['nombre']}\n"
            mensaje += f"  → {alt['farmacia']} — ${alt['precio']:.2f}\n"
            if alt.get('url'):
                mensaje += f"  👉 {alt['url']}\n"
            mensaje += "\n"
    else:
        mensaje += "No encontramos alternativas en nuestra base,\n"
        mensaje += "pero puedes preguntar por: amoxicilina, ibuprofeno, paracetamol (según el caso).\n"
        mensaje += "Consulta con tu farmacéutico.\n\n"
    
    # 5. Acción sugerida (NUNCA terminar sin acción)
    mensaje += "¿Quieres buscar el precio exacto\n"
    mensaje += "de este medicamento? Escribe \"sí\"\n"
    mensaje += "y te avisamos cuando lo tengamos."
    
    return mensaje

def manejar_pregunta_seguimiento(pregunta: str, contexto: dict) -> str:
    pregunta = pregunta.lower()
    if pregunta in ['sí', 'si']:
        return "¡Perfecto! Te avisaremos cuando tengamos precios para este medicamento. Mientras tanto, puedes consultar en tu farmacia más cercana."
    elif pregunta == 'no':
        return "Entendido. ¿Hay algo más en lo que pueda ayudarte? Recuerda que puedes buscar otro medicamento."
    elif 'genérico' in pregunta or 'generico' in pregunta:
        alternativas = contexto.get('alternativas', [])
        if alternativas:
            respuesta = "Estos son los genéricos equivalentes:\n"
            for alt in alternativas[:5]:
                respuesta += f"• {alt['nombre']} — ${alt['precio']:.2f} en {alt['farmacia']}\n"
            return respuesta
        else:
            return "No encontramos genéricos en nuestra base, pero puedes consultar en tu farmacia más cercana. Pregunta por el principio activo."
    elif 'tarda' in pregunta or 'cuánto' in pregunta:
        return "Normalmente actualizamos los precios en 24-48 horas. Te notificaremos en cuanto tengamos novedades. ¿Quieres que te avise?"
    else:
        return "No entendí tu pregunta. Por favor, reformúlala o escríbeme 'sí' para que te avise, 'no' para cancelar, o pregunta por genéricos."

def limpiar_contexto_expirado():
    ahora = datetime.now(timezone.utc)
    expirados = [k for k, v in user_context.items() 
                 if ahora - v.get('timestamp', ahora) > CONTEXTO_EXPIRACION]
    for k in expirados:
        del user_context[k]

# ------------------------------------------------------------
#  FUNCIÓN DE FORMATEO (sin cambios)
# ------------------------------------------------------------
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
        plataformas = set()
        for p in delivery:
            fuente = p['fuente'].lower()
            if 'rappi' in fuente:
                plataformas.add('rappi')
            elif 'ubereats' in fuente:
                plataformas.add('ubereats')

        if len(plataformas) == 1:
            if 'rappi' in plataformas:
                titulo = "🛵 *A domicilio vía Rappi*"
            elif 'ubereats' in plataformas:
                titulo = "🛵 *A domicilio vía Uber Eats*"
            else:
                titulo = "🛵 *A domicilio:*"
        else:
            titulo = "🛵 *A domicilio vía Rappi / Uber Eats*"

        lines.append(titulo)

        for p in delivery[:3]:
            fuente = p['fuente'].lower()
            url = p.get('url') or p.get('link_producto')
            if not url or 'add-product-icon' in url:
                busqueda = nombre_generico.replace(' ', '+')
                if 'rappi' in fuente:
                    url = f"https://www.rappi.com.mx/search?q={busqueda}"
                elif 'ubereats' in fuente:
                    url = f"https://ubereats.com/mx/search?q={busqueda}"
                else:
                    url = None

            linea = f"  {p['farmacia']} — ${p['precio']:.2f}"
            lines.append(linea)
            entrega = p.get('entrega_estimada', '25-35 min')
            lines.append(f"  🕐 Entrega en {entrega}")
            if url and url != '#' and url is not None:
                lines.append(f"  👉 Pedir aquí: {url}")
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

# ------------------------------------------------------------
#  WEBHOOK PRINCIPAL
# ------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    resp = MessagingResponse()
    msg = resp.message()
    try:
        incoming_msg = request.form.get("Body", "").strip()
        sender = request.form.get("From", "desconocido")
        logging.info(f"Mensaje de {sender}: {incoming_msg}")

        limpiar_contexto_expirado()

        if is_limit_reached():
            msg.body("Alcanzamos el límite de consultas por hoy. Vuelve mañana.")
            logging.warning(f"Límite diario alcanzado, rechazando mensaje de {sender}")
            return Response(str(resp), mimetype="application/xml")

        if not incoming_msg:
            msg.body("Por favor, envía el nombre de un medicamento.")
            return Response(str(resp), mimetype="application/xml")

        # ---------- Manejo de preguntas de seguimiento ----------
        contexto = user_context.get(sender)
        if contexto:
            pregunta = incoming_msg.lower()
            seguimiento_keywords = ['sí', 'si', 'no', 'genérico', 'generico', 'tarda', 'demora', 'cuánto', 'hay']
            if any(keyword in pregunta for keyword in seguimiento_keywords):
                respuesta = manejar_pregunta_seguimiento(pregunta, contexto)
                msg.body(respuesta)
                return Response(str(resp), mimetype="application/xml")
        # ---------------------------------------------------------

        # Procesar nueva búsqueda
        resultado = normalizer.normalizar(incoming_msg)
        if "error" in resultado:
            msg.body(f"❌ Error: {resultado['error']}")
            return Response(str(resp), mimetype="application/xml")

        nombre_generico = resultado.get('nombre_generico', '').lower()
        nombre_ingresado = resultado.get('nombre_ingresado', incoming_msg).lower()
        medicamento_ref = nombre_generico if nombre_generico else nombre_ingresado

        # Obtener precios recientes
        precios_recientes = get_resumen(nombre_generico) + get_resumen(nombre_ingresado)
        logging.info(f"Registros recientes obtenidos: {len(precios_recientes)}")

        if not precios_recientes:
            logging.info("No hay registros recientes, buscando históricos...")
            historicos_todos = get_last_precios(nombre_generico, limit=20) + get_last_precios(nombre_ingresado, limit=20)
            seen = set()
            precios_recientes = []
            for p in historicos_todos:
                key = (p.get('farmacia'), p.get('precio'), p.get('nombre_raw'))
                if key not in seen:
                    seen.add(key)
                    precios_recientes.append(p)
            logging.info(f"Registros históricos obtenidos: {len(precios_recientes)}")

        # Filtros
        conn = get_connection()
        try:
            filtrados_coherencia = []
            for p in precios_recientes:
                if validar_coherencia_producto(p.get('nombre_raw', ''), medicamento_ref):
                    filtrados_coherencia.append(p)
                else:
                    logging.info(f"Descartado por incoherencia: {p.get('nombre_raw', '')[:40]} vs {medicamento_ref}")

            filtrados_precio = []
            for p in filtrados_coherencia:
                if validar_precio(p['precio'], medicamento_ref, conn):
                    filtrados_precio.append(p)
                else:
                    logging.info(f"Descartado por precio anómalo: ${p['precio']} para {medicamento_ref}")

            mejores = {}
            for p in filtrados_precio:
                farmacia_norm = normalizar_farmacia(p['farmacia']).lower()
                if farmacia_norm not in mejores or p['fecha'] > mejores[farmacia_norm]['fecha']:
                    mejores[farmacia_norm] = p
            precios_depurados = list(mejores.values())
            logging.info(f"Después de deduplicación: {len(precios_depurados)}")
        finally:
            conn.close()

        delivery = [p for p in precios_depurados if p.get('fuente', '').lower() in ['agente_rappi', 'agente_ubereats']]
        farmacias = [p for p in precios_depurados if p.get('fuente', '').lower() not in ['agente_rappi', 'agente_ubereats']]

        farmacias.sort(key=lambda x: x['precio'])
        delivery.sort(key=lambda x: x['precio'])

        if farmacias or delivery:
            respuesta = formatear_respuesta(nombre_generico, farmacias, delivery)
            msg.body(respuesta)
            # Guardar contexto
            user_context[sender] = {
                'medicamento_buscado': nombre_ingresado,
                'nombre_generico': nombre_generico,
                'principio_activo': resultado.get('principio_activo', nombre_generico),
                'requiere_receta': resultado.get('requiere_receta', False),
                'alternativas': [],
                'timestamp': datetime.now(timezone.utc)
            }
        else:
            # ---------- FALLBACK INTELIGENTE ----------
            # Usamos la función mejorada para obtener el principio activo
            principio_activo = obtener_principio_activo_mejorado(resultado, nombre_generico, nombre_ingresado)
            logging.info(f"🔍 Principio activo para búsqueda de alternativas: {principio_activo}")

            alternativas = get_alternativas(principio_activo, limit=5)
            logging.info(f"📦 Alternativas encontradas: {len(alternativas)}")
            if alternativas:
                logging.info(f"Primera alternativa: {alternativas[0]['nombre']} - ${alternativas[0]['precio']}")

            requiere_receta = resultado.get('requiere_receta', False)

            mensaje = construir_mensaje_fallback(
                nombre_ingresado,
                nombre_generico,
                requiere_receta,
                alternativas,
                principio_activo
            )
            msg.body(mensaje)

            # Guardar contexto con alternativas
            user_context[sender] = {
                'medicamento_buscado': nombre_ingresado,
                'nombre_generico': nombre_generico,
                'principio_activo': principio_activo,
                'requiere_receta': requiere_receta,
                'alternativas': alternativas,
                'timestamp': datetime.now(timezone.utc)
            }

        if increment_and_check_limit():
            mensaje_limite = (
                f"⚠️ *Dr. Ahorro* — Límite diario al 80%\n"
                f"Hoy se han procesado {LIMITE_NOTIFICACION} mensajes de {LIMITE_DIARIO} permitidos.\n"
                f"Revisa el uso del sandbox de Twilio."
            )
            send_telegram_message(mensaje_limite)

    except Exception as e:
        logging.error(f"Error crítico en webhook: {e}", exc_info=True)
        if "429" in str(e) or "Too Many Requests" in str(e):
            msg.body("Alcanzamos el límite de consultas por hoy. Vuelve mañana.")
        else:
            msg.body("Ocurrió un error, intenta de nuevo.")

    return Response(str(resp), mimetype="application/xml")

# ------------------------------------------------------------
#  EJECUCIÓN
# ------------------------------------------------------------
def run_whatsapp_bot(port=5000):
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)