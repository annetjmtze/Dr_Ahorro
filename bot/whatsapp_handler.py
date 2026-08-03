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
    get_usuario, save_zona_texto, save_zona_gps, clear_zona,
    guardar_analisis  # ✅ Importada desde database
)
from bot.counter import increment_and_check_limit, is_limit_reached, LIMITE_DIARIO, LIMITE_NOTIFICACION
from bot.telegram_notifier import send_telegram_message
from data.agents.maps_agent import obtener_mapa_para_zona_sync

# ✅ Motor de costo‑beneficio
from data.analytics.costo_beneficio import calcular_recomendacion

load_dotenv()

IS_PROD = os.getenv("DATABASE_URL") is not None
init_db()

app = Flask(__name__)
normalizer = MedicamentoNormalizer()
logging.basicConfig(level=logging.INFO)

user_context = {}
CONTEXTO_EXPIRACION = timedelta(minutes=30)
pending_zone = {}  # Número -> medicamento pendiente

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
    """
    Mensaje cuando no hay precios recientes en la BD.
    No revela arquitectura interna, solo da opciones útiles.
    """
    mensaje = ""
    if requiere_receta:
        mensaje += "⚠️ *Este medicamento requiere receta médica*\n\n"
    
    mensaje += f"💊 *{nombre_ingresado.title()}*\n"
    mensaje += "No tenemos información de precios en este momento,\n"
    mensaje += "pero te compartimos algunos medicamentos similares que\n"
    mensaje += "puedes consultar en tu farmacia más cercana:\n\n"
    
    if alternativas:
        for alt in alternativas[:5]:
            mensaje += f"• {alt['nombre']}\n"
            mensaje += f"  → {alt['farmacia']} — ${alt['precio']:.2f}\n"
            if alt.get('url'):
                mensaje += f"  👉 {alt['url']}\n"
            mensaje += "\n"
    else:
        mensaje += "No tenemos registros de este medicamento,\n"
        mensaje += "pero puedes preguntar por alternativas como:\n"
        mensaje += "amoxicilina, ibuprofeno, paracetamol (según el caso).\n"
        mensaje += "Consulta con tu farmacéutico.\n\n"
    
    mensaje += "¿Quieres que te avisemos cuando tengamos precios?\n"
    mensaje += "Escribe *sí* y te notificaremos."
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
        return None  # No es una pregunta de seguimiento válida

def limpiar_contexto_expirado():
    ahora = datetime.now(timezone.utc)
    expirados = [k for k, v in user_context.items() 
                 if ahora - v.get('timestamp', ahora) > CONTEXTO_EXPIRACION]
    for k in expirados:
        del user_context[k]

# ------------------------------------------------------------
#  FORMATEO DE RESPUESTA
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

        # ---------- COMANDO /zona ----------
        if incoming_msg.lower() == "/zona":
            clear_zona(sender)
            user_context.pop(sender, None)
            pending_zone.pop(sender, None)
            msg = resp.message()
            msg.body("📍 Para actualizar tu zona, escribe tu colonia y ciudad (ej. 'Del Valle, CDMX') o tu código postal (5 dígitos).\n"
                     "También puedes tocar el clip 📎 y compartir tu ubicación.")
            return Response(str(resp), mimetype="application/xml")

        # ---------- DETECCIÓN DE CP (siempre) ----------
        es_cp = incoming_msg.isdigit() and len(incoming_msg) in [5, 6]

        if es_cp and sender not in pending_zone:
            save_zona_texto(sender, None, incoming_msg, None)
            user_context.pop(sender, None)
            pending_zone.pop(sender, None)
            msg = resp.message()
            msg.body(f"✅ Código postal {incoming_msg} guardado. Ahora escribe el nombre de un medicamento para buscar precios.")
            return Response(str(resp), mimetype="application/xml")

        # ---------- GPS ----------
        if is_gps and sender not in pending_zone:
            save_zona_gps(sender, float(lat), float(lon))
            user_context.pop(sender, None)
            pending_zone.pop(sender, None)
            msg = resp.message()
            msg.body("✅ Ubicación GPS guardada. Ahora escribe el nombre de un medicamento para buscar precios.")
            return Response(str(resp), mimetype="application/xml")

        # ---------- RESPUESTA A ZONA ----------
        if sender in pending_zone:
            medicamento_pendiente = pending_zone.pop(sender)
            zona_texto = None

            if is_gps:
                save_zona_gps(sender, float(lat), float(lon))
                zona_texto = f"GPS ({float(lat):.4f}, {float(lon):.4f})"
                incoming_msg = medicamento_pendiente
            else:
                texto = incoming_msg
                if texto.isdigit() and len(texto) in [5, 6]:
                    save_zona_texto(sender, None, texto, None)
                    zona_texto = f"CP {texto}"
                    incoming_msg = medicamento_pendiente
                elif ',' in texto:
                    colonia, ciudad = texto.split(',', 1)
                    colonia = colonia.strip()
                    ciudad = ciudad.strip()
                    save_zona_texto(sender, colonia, None, ciudad)
                    zona_texto = f"{colonia}, {ciudad}"
                    incoming_msg = medicamento_pendiente
                else:
                    save_zona_texto(sender, texto, None, None)
                    zona_texto = texto
                    incoming_msg = medicamento_pendiente

            user_context.pop(sender, None)

        # ---------- VERIFICAR ZONA ----------
        usuario = get_usuario(sender)
        tiene_zona = usuario and (
            usuario.get('colonia') is not None or 
            usuario.get('codigo_postal') is not None or 
            usuario.get('latitud') is not None
        )

        if not tiene_zona and sender not in pending_zone:
            pending_zone[sender] = incoming_msg
            msg = resp.message()
            msg.body("📍 Para mostrarte las farmacias más cercanas, ¿en qué zona buscas?\n"
                     "Escribe tu colonia y ciudad (ej. 'Del Valle, CDMX') o tu código postal (5 dígitos).\n"
                     "También puedes tocar el clip 📎 y compartir tu ubicación.")
            return Response(str(resp), mimetype="application/xml")

        # ---------- PROCESAR BÚSQUEDA ----------
        contexto = user_context.get(sender)
        if contexto:
            pregunta = incoming_msg.lower()
            seguimiento_keywords = ['sí', 'si', 'no', 'genérico', 'generico', 'tarda', 'demora', 'cuánto', 'hay']
            if any(keyword in pregunta for keyword in seguimiento_keywords):
                respuesta = manejar_pregunta_seguimiento(pregunta, contexto)
                if respuesta:
                    msg = resp.message()
                    msg.body(respuesta)
                    return Response(str(resp), mimetype="application/xml")
                else:
                    user_context.pop(sender, None)
            else:
                user_context.pop(sender, None)

        # Normalizar medicamento
        resultado = normalizer.normalizar(incoming_msg)
        if "error" in resultado:
            msg = resp.message()
            msg.body(f"❌ Error: {resultado['error']}")
            return Response(str(resp), mimetype="application/xml")

        nombre_generico = resultado.get('nombre_generico', '').lower()
        nombre_ingresado = resultado.get('nombre_ingresado', incoming_msg).lower()
        medicamento_ref = nombre_generico if nombre_generico else nombre_ingresado

        urgente = resultado.get('urgente', False)
        logging.info(f"Urgencia detectada: {urgente}")

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

        # Separar delivery y farmacias
        delivery = [p for p in precios_depurados if p.get('fuente', '').lower() in ['agente_rappi', 'agente_ubereats']]
        farmacias = [p for p in precios_depurados if p.get('fuente', '').lower() not in ['agente_rappi', 'agente_ubereats']]

        farmacias.sort(key=lambda x: x['precio'])
        delivery.sort(key=lambda x: x['precio'])

        # ------------------------------------------------------------
        #  MOTOR DE COSTO‑BENEFICIO
        # ------------------------------------------------------------
        farmacias_bd = [{"nombre": p["farmacia"], "precio": p["precio"]} for p in farmacias]
        ENVIO_ESTIMADO = 30.0
        delivery_opts = [{"nombre": p["farmacia"], "precio_total": p["precio"] + ENVIO_ESTIMADO} for p in delivery]
        farmacias_mapa = []  # Pendiente de implementar con OCR

        recomendacion = calcular_recomendacion(
            farmacias_bd=farmacias_bd,
            delivery=delivery_opts,
            farmacias_mapa=farmacias_mapa,
            urgente=urgente
        )

        # ------------------------------------------------------------
        #  OBTENER ZONA Y MAPA
        # ------------------------------------------------------------
        usuario_actual = get_usuario(sender)
        if usuario_actual:
            if usuario_actual.get('colonia') and usuario_actual.get('ciudad'):
                colonia = usuario_actual['colonia']
                ciudad = usuario_actual['ciudad']
                zona_texto = f"{colonia}, {ciudad}"
                colonia_para_mapa = colonia
                ciudad_para_mapa = ciudad
                lat_para_mapa = None
                lon_para_mapa = None
            elif usuario_actual.get('colonia') and not usuario_actual.get('ciudad'):
                colonia = usuario_actual['colonia']
                zona_texto = colonia
                colonia_para_mapa = colonia
                ciudad_para_mapa = None
                lat_para_mapa = None
                lon_para_mapa = None
            elif usuario_actual.get('codigo_postal'):
                cp = usuario_actual['codigo_postal']
                zona_texto = f"CP {cp}"
                colonia_para_mapa = cp
                ciudad_para_mapa = None
                lat_para_mapa = None
                lon_para_mapa = None
            elif usuario_actual.get('latitud') is not None:
                lat = usuario_actual['latitud']
                lon = usuario_actual['longitud']
                zona_texto = f"GPS ({lat:.4f}, {lon:.4f})"
                colonia_para_mapa = None
                ciudad_para_mapa = None
                lat_para_mapa = lat
                lon_para_mapa = lon
            else:
                zona_texto = "tu zona"
                colonia_para_mapa = None
                ciudad_para_mapa = None
                lat_para_mapa = None
                lon_para_mapa = None
        else:
            zona_texto = None
            colonia_para_mapa = None
            ciudad_para_mapa = None
            lat_para_mapa = None
            lon_para_mapa = None

        # Generar mapa
        mapa_url = None
        if colonia_para_mapa and ciudad_para_mapa:
            try:
                logging.info(f"🗺️ Generando mapa para colonia: {colonia_para_mapa}, ciudad: {ciudad_para_mapa}")
                mapa_url = obtener_mapa_para_zona_sync(zona=colonia_para_mapa, ciudad=ciudad_para_mapa)
            except Exception as e:
                logging.error(f"❌ Error al obtener mapa: {e}")
                mapa_url = None
        elif colonia_para_mapa and not ciudad_para_mapa:
            try:
                logging.info(f"🗺️ Generando mapa para colonia/CP: {colonia_para_mapa}")
                mapa_url = obtener_mapa_para_zona_sync(zona=colonia_para_mapa)
            except Exception as e:
                logging.error(f"❌ Error al obtener mapa: {e}")
                mapa_url = None
        elif lat_para_mapa is not None and lon_para_mapa is not None:
            try:
                logging.info(f"🗺️ Generando mapa para GPS: {lat_para_mapa}, {lon_para_mapa}")
                mapa_url = obtener_mapa_para_zona_sync(lat=lat_para_mapa, lon=lon_para_mapa)
            except Exception as e:
                logging.error(f"❌ Error al obtener mapa: {e}")
                mapa_url = None

        if mapa_url:
            logging.info(f"✅ Mapa obtenido: {mapa_url}")
        else:
            logging.info("ℹ️ No se pudo obtener mapa (falló o no hay caché válido)")

        # ------------------------------------------------------------
        #  EXTRAER PRECIOS Y NORMALIZAR AHORRO (CORRECCIÓN CLAVE)
        # ------------------------------------------------------------
        precio_fisica = farmacias[0]['precio'] if farmacias else None
        precio_rappi = delivery[0]['precio'] if delivery else None

        # ✅ Normalizar ahorro_calculado para evitar NULL en reporte
        ahorro_calculado = recomendacion.get("ahorro_vs_delivery", 0.0)
        if ahorro_calculado is None:
            ahorro_calculado = 0.0
        try:
            ahorro_calculado = float(ahorro_calculado)
        except (TypeError, ValueError):
            ahorro_calculado = 0.0

        opcion_ganadora = recomendacion.get("opcion_ganadora")
        opcion_recomendada = opcion_ganadora
        precio_recomendado = None
        if opcion_recomendada == 'farmacia' and precio_fisica is not None:
            precio_recomendado = precio_fisica
        elif opcion_recomendada == 'delivery' and precio_rappi is not None:
            precio_recomendado = precio_rappi

        # ------------------------------------------------------------
        #  GUARDAR ANÁLISIS (con ahorro ya normalizado)
        # ------------------------------------------------------------
        try:
            guardar_analisis(
                usuario=sender,
                medicamento=nombre_generico or nombre_ingresado,
                urgente=urgente,
                opcion_ganadora=opcion_ganadora,
                ahorro_calculado=ahorro_calculado,   # <-- Siempre float
                zona=zona_texto,
                opcion_recomendada=opcion_recomendada,
                precio_recomendado=precio_recomendado,
                precio_rappi=precio_rappi,
                precio_fisica=precio_fisica,
                fecha=datetime.now(timezone.utc)
            )
        except Exception as e:
            logging.error(f"Error guardando análisis en BD: {e}")

        # ------------------------------------------------------------
        #  CONSTRUIR RESPUESTA
        # ------------------------------------------------------------
        if farmacias or delivery:
            texto_ranking = formatear_respuesta(nombre_generico, farmacias, delivery, zona_texto)
            texto_respuesta = texto_ranking + "\n\n" + recomendacion["texto_recomendacion"]
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
            texto_respuesta += "\n\n" + recomendacion["texto_recomendacion"]
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