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
    get_connection, get_precios,
    get_usuario, save_zona_texto, save_zona_gps, clear_zona
)
from bot.counter import increment_and_check_limit, is_limit_reached, LIMITE_DIARIO, LIMITE_NOTIFICACION
from bot.telegram_notifier import send_telegram_message

# --- NUEVA IMPORTACIÓN PARA MAPAS ---
from data.agents.maps_agent import obtener_mapa_para_zona_sync

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

# --- Diccionarios para onboarding ---
pending_zone = {}         # medicamento pendiente
pending_colonia = {}      # colonia/cp pendiente (cuando falta ciudad)

# ------------------------------------------------------------
#  FUNCIONES AUXILIARES
# ------------------------------------------------------------

def obtener_principio_activo_mejorado(resultado, nombre_generico, nombre_ingresado):
    if resultado.get('principio_activo'):
        return resultado['principio_activo']
    nombre_lower = nombre_ingresado.lower()
    if 'clavulánico' in nombre_lower or 'clavulanico' in nombre_lower:
        return 'amoxicilina'
    if 'aspirina' in nombre_lower:
        return 'aspirina'
    if 'ibuprofeno' in nombre_lower:
        return 'ibuprofeno'
    if 'paracetamol' in nombre_lower:
        return 'paracetamol'
    return nombre_generico

def get_alternativas(principio_activo: str, limit: int = 5):
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
    if requiere_receta:
        mensaje += "⚠️ *Este medicamento requiere receta médica*\n\n"
    mensaje += f"💊 *{nombre_ingresado.title()}*\n"
    mensaje += "Aún no tenemos precios en tu zona,\n"
    mensaje += "pero encontramos estos similares:\n\n"
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
#  FUNCIÓN DE FORMATEO
# ------------------------------------------------------------
def formatear_respuesta(nombre_generico: str, farmacias: list, delivery: list, zona_texto: str = None) -> str:
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

    if zona_texto:
        lines.append(f"\n📍 Buscando en {zona_texto} · Escribe /zona para cambiar.")
    else:
        lines.append("\n↩️ Escribe otro medicamento para comparar")
    return "\n".join(lines)

# ------------------------------------------------------------
#  WEBHOOK PRINCIPAL
# ------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    resp = MessagingResponse()
    try:
        incoming_msg = request.form.get("Body", "").strip()
        sender = request.form.get("From", "desconocido")
        lat = request.form.get("Latitude")
        lon = request.form.get("Longitude")
        is_gps = (lat is not None and lon is not None)

        logging.info(f"Mensaje de {sender}: {incoming_msg} (GPS: {is_gps})")

        limpiar_contexto_expirado()

        if is_limit_reached():
            msg = resp.message()
            msg.body("Alcanzamos el límite de consultas por hoy. Vuelve mañana.")
            return Response(str(resp), mimetype="application/xml")

        if not incoming_msg and not is_gps:
            msg = resp.message()
            msg.body("Por favor, envía el nombre de un medicamento.")
            return Response(str(resp), mimetype="application/xml")

        # ---------- MANEJO DE COMANDO /zona ----------
        if incoming_msg.lower() == "/zona":
            clear_zona(sender)
            msg = resp.message()
            msg.body("📍 Para mostrarte las farmacias más cercanas, ¿en qué zona buscas? Escribe tu colonia o código postal, o toca el clip 📎 y comparte tu ubicación.")
            pending_zone.pop(sender, None)
            pending_colonia.pop(sender, None)
            return Response(str(resp), mimetype="application/xml")

        # ---------- MANEJO DE GPS ----------
        if is_gps and sender not in pending_zone:
            save_zona_gps(sender, float(lat), float(lon))
            msg = resp.message()
            msg.body("✅ Ubicación GPS guardada. Ahora puedes buscar medicamentos y te mostraré precios en tu zona.")
            return Response(str(resp), mimetype="application/xml")

        # ---------- SI EL USUARIO ESTÁ ESPERANDO LA CIUDAD ----------
        if sender in pending_colonia:
            # La respuesta es la ciudad
            ciudad = incoming_msg
            colonia_info = pending_colonia.pop(sender)
            medicamento_pendiente = pending_zone.pop(sender, None)

            # Guardar con colonia y ciudad
            if colonia_info['tipo'] == 'colonia':
                save_zona_texto(sender, colonia_info['valor'], None, ciudad)
                zona_texto = f"{colonia_info['valor']}, {ciudad}"
            else:  # CP
                save_zona_texto(sender, None, colonia_info['valor'], ciudad)
                zona_texto = f"CP {colonia_info['valor']}, {ciudad}"

            incoming_msg = medicamento_pendiente
            # Continuar con la búsqueda

        # ---------- SI EL USUARIO ESTÁ EN pending_zone (respondiendo colonia/CP) ----------
        elif sender in pending_zone:
            medicamento_pendiente = pending_zone.pop(sender)

            if is_gps:
                save_zona_gps(sender, float(lat), float(lon))
                zona_texto = "tu ubicación GPS"
                incoming_msg = medicamento_pendiente
            else:
                # Intentar extraer colonia y ciudad (formato: "colonia, ciudad")
                partes = incoming_msg.split(',')
                if len(partes) > 1:
                    colonia = partes[0].strip()
                    ciudad = partes[1].strip()
                    # Guardar directamente
                    save_zona_texto(sender, colonia, None, ciudad)
                    zona_texto = f"{colonia}, {ciudad}"
                    incoming_msg = medicamento_pendiente
                else:
                    # Solo colonia o CP -> guardar temporal y preguntar ciudad
                    if incoming_msg.isdigit() and len(incoming_msg) in [5, 6]:
                        # Es CP
                        pending_colonia[sender] = {'tipo': 'cp', 'valor': incoming_msg}
                        msg = resp.message()
                        msg.body("📍 ¿En qué ciudad se encuentra este código postal? (ej. Uruapan, Morelia)")
                        return Response(str(resp), mimetype="application/xml")
                    else:
                        # Es colonia
                        pending_colonia[sender] = {'tipo': 'colonia', 'valor': incoming_msg}
                        msg = resp.message()
                        msg.body("📍 ¿En qué ciudad se encuentra esta colonia? (ej. Uruapan, Morelia)")
                        return Response(str(resp), mimetype="application/xml")

        # ---------- A PARTIR DE AQUÍ EL USUARIO TIENE ZONA GUARDADA ----------
        usuario = get_usuario(sender)
        tiene_zona = usuario and (usuario.get('colonia') is not None or usuario.get('latitud') is not None)

        # Si no tiene zona, preguntar
        if not tiene_zona and sender not in pending_zone:
            pending_zone[sender] = incoming_msg
            msg = resp.message()
            msg.body("📍 Para mostrarte las farmacias más cercanas, ¿en qué zona buscas? Escribe tu colonia o código postal, o toca el clip 📎 y comparte tu ubicación.")
            return Response(str(resp), mimetype="application/xml")

        # --- PROCESAR BÚSQUEDA DE MEDICAMENTO ---

        # Manejo de preguntas de seguimiento
        contexto = user_context.get(sender)
        if contexto:
            pregunta = incoming_msg.lower()
            seguimiento_keywords = ['sí', 'si', 'no', 'genérico', 'generico', 'tarda', 'demora', 'cuánto', 'hay']
            if any(keyword in pregunta for keyword in seguimiento_keywords):
                respuesta = manejar_pregunta_seguimiento(pregunta, contexto)
                msg = resp.message()
                msg.body(respuesta)
                return Response(str(resp), mimetype="application/xml")

        # Normalizar medicamento
        resultado = normalizer.normalizar(incoming_msg)
        if "error" in resultado:
            msg = resp.message()
            msg.body(f"❌ Error: {resultado['error']}")
            return Response(str(resp), mimetype="application/xml")

        nombre_generico = resultado.get('nombre_generico', '').lower()
        nombre_ingresado = resultado.get('nombre_ingresado', incoming_msg).lower()
        medicamento_ref = nombre_generico if nombre_generico else nombre_ingresado

        # Obtener precios
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
                if p.get('fuente', '').lower() in ['agente_rappi', 'agente_ubereats']:
                    filtrados_coherencia.append(p)
                elif validar_coherencia_producto(p.get('nombre_raw', ''), medicamento_ref):
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
                key = (normalizar_farmacia(p['farmacia']).lower(), p.get('fuente', '').lower())
                if key not in mejores or p['fecha'] > mejores[key]['fecha']:
                    mejores[key] = p
            precios_depurados = list(mejores.values())
            logging.info(f"Después de deduplicación: {len(precios_depurados)}")
        finally:
            conn.close()

        delivery = [p for p in precios_depurados if p.get('fuente', '').lower() in ['agente_rappi', 'agente_ubereats']]
        farmacias = [p for p in precios_depurados if p.get('fuente', '').lower() not in ['agente_rappi', 'agente_ubereats']]

        farmacias.sort(key=lambda x: x['precio'])
        delivery.sort(key=lambda x: x['precio'])

        # --- OBTENER ZONA DEL USUARIO (COLONIA + CIUDAD) ---
        usuario_actual = get_usuario(sender)
        if usuario_actual:
            if usuario_actual.get('colonia'):
                colonia = usuario_actual['colonia']
                ciudad = usuario_actual.get('ciudad') or "Ciudad de México"
                zona_texto = f"{colonia}, {ciudad}"
                colonia_para_mapa = colonia
                ciudad_para_mapa = ciudad
            elif usuario_actual.get('latitud') is not None:
                zona_texto = f"GPS ({usuario_actual['latitud']:.4f}, {usuario_actual['longitud']:.4f})"
                colonia_para_mapa = None
                ciudad_para_mapa = None
            else:
                zona_texto = "tu zona"
                colonia_para_mapa = None
                ciudad_para_mapa = None
        else:
            zona_texto = None
            colonia_para_mapa = None
            ciudad_para_mapa = None

        # --- GENERAR MAPA ---
        mapa_url = None
        if colonia_para_mapa and ciudad_para_mapa:
            try:
                logging.info(f"🗺️ Generando mapa para colonia: {colonia_para_mapa}, ciudad: {ciudad_para_mapa}")
                mapa_url = obtener_mapa_para_zona_sync(colonia_para_mapa, ciudad=ciudad_para_mapa)
                if mapa_url:
                    logging.info(f"✅ Mapa obtenido: {mapa_url}")
                else:
                    logging.info("ℹ️ No se pudo obtener mapa (falló o no hay caché válido)")
            except Exception as e:
                logging.error(f"❌ Error al obtener mapa: {e}")
                mapa_url = None

        # --- CONSTRUIR RESPUESTA DE TEXTO ---
        if farmacias or delivery:
            texto_respuesta = formatear_respuesta(nombre_generico, farmacias, delivery, zona_texto)
            user_context[sender] = {
                'medicamento_buscado': nombre_ingresado,
                'nombre_generico': nombre_generico,
                'principio_activo': resultado.get('principio_activo', nombre_generico),
                'requiere_receta': resultado.get('requiere_receta', False),
                'alternativas': [],
                'timestamp': datetime.now(timezone.utc)
            }
        else:
            principio_activo = obtener_principio_activo_mejorado(resultado, nombre_generico, nombre_ingresado)
            logging.info(f"🔍 Principio activo para búsqueda de alternativas: {principio_activo}")
            alternativas = get_alternativas(principio_activo, limit=5)
            logging.info(f"📦 Alternativas encontradas: {len(alternativas)}")
            requiere_receta = resultado.get('requiere_receta', False)
            texto_respuesta = construir_mensaje_fallback(
                nombre_ingresado,
                nombre_generico,
                requiere_receta,
                alternativas,
                principio_activo
            )
            if zona_texto:
                texto_respuesta += f"\n📍 Buscando en {zona_texto} · Escribe /zona para cambiar."
            user_context[sender] = {
                'medicamento_buscado': nombre_ingresado,
                'nombre_generico': nombre_generico,
                'principio_activo': principio_activo,
                'requiere_receta': requiere_receta,
                'alternativas': alternativas,
                'timestamp': datetime.now(timezone.utc)
            }

        # --- ENVIAR RESPUESTA (IMAGEN + TEXTO) ---
        if mapa_url:
            msg_mapa = resp.message()
            msg_mapa.media(mapa_url)
            logging.info(f"🖼️ Enviando imagen del mapa a {sender}")

        msg_texto = resp.message()
        msg_texto.body(texto_respuesta)

        if increment_and_check_limit():
            mensaje_limite = (
                f"⚠️ *Dr. Ahorro* — Límite diario al 80%\n"
                f"Hoy se han procesado {LIMITE_NOTIFICACION} mensajes de {LIMITE_DIARIO} permitidos.\n"
                f"Revisa el uso del sandbox de Twilio."
            )
            send_telegram_message(mensaje_limite)

    except Exception as e:
        logging.error(f"Error crítico en webhook: {e}", exc_info=True)
        msg = resp.message()
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