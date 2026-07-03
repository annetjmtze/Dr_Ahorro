import os
import logging
import json
import traceback
from dotenv import load_dotenv
import anthropic
from telegram import Update
from telegram import constants
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Configuración de logs para ver qué pasa en consola
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- INICIALIZACIÓN GLOBAL DE ANTHROPIC ---
# Al definirlo aquí, se crea una única instancia que reutilizará las conexiones (Connection Pooling)
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    logging.warning("Advertencia: No se encontró la variable de entorno ANTHROPIC_API_KEY en la carga inicial.")
    client = None
else:
    client = anthropic.Anthropic(api_key=API_KEY)

# --- COMANDOS DEL BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /start con un saludo."""
    await update.message.reply_text(
        "¡Hola! Soy tu bot asistente. 👋\n"
        "Puedes usar /ayuda para ver lo que puedo hacer."
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /ayuda con instrucciones."""
    await update.message.reply_text(
        "🤖 *Instrucciones de uso:*\n\n"
        "1️⃣ */medicamento <nombre>*: Busca información sobre un medicamento en México.\n"
        "   _Ejemplo: `/medicamento Paracetamol`_\n\n"
        "2️⃣ *Cualquier otro mensaje*: Repetiré el texto que me envíes (función de eco).\n\n"
        "Usa /start para reiniciar o /ayuda para ver este mensaje de nuevo.",
        parse_mode="Markdown",
    )

# --- LÓGICA DE INTEGRACIÓN CON ANTHROPIC ---

async def buscar_medicamento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca información de un medicamento usando la API de Anthropic y responde con texto legible."""
    global client  # Hacemos referencia al cliente global
    
    if not context.args:
        await update.message.reply_text("Por favor, dime qué medicamento buscar. Ejemplo: /medicamento Paracetamol")
        return

    nombre_medicamento = " ".join(context.args)
    
    # Indicador de "escribiendo..." para mejorar UX
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    # --- VALIDACIÓN DE LA API KEY / CLIENTE ---
    if not client:
        logging.error("Error: El cliente de Anthropic no está inicializado porque falta la API KEY.")
        await update.message.reply_text("Error de configuración del bot. Contacta al administrador.")
        return

    try:
        # Realizar la llamada a la API usando el cliente reutilizable
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system="""
Eres un asistente experto en medicamentos en México.
Da una descripción breve.
Tu respuesta DEBE ser únicamente un objeto JSON válido, sin texto adicional antes o después.
El JSON debe tener la siguiente estructura:
{
  "nombre ingresado": "string",
  "nombre_generico": "string",
  "uso_principal": "string",
  "requiere_receta": boolean
}
""",
            messages=[
                {"role": "user", "content": nombre_medicamento}
            ]
        )

        # Extraer y limpiar el texto
        response_text = message.content[0].text
        logging.info(f"Respuesta recibida de Anthropic: {response_text}")

        # Limpieza de bloques de código de tipo ```json si Claude los incluye
        response_text = response_text.replace("```json", "")
        response_text = response_text.replace("```", "")
        response_text = response_text.strip()

        # Parsear el JSON
        datos = json.loads(response_text)

        # Extraer campos con respaldos por si no vienen
        nombre = datos.get("nombre ingresado", nombre_medicamento).capitalize()
        uso = datos.get("uso_principal", "No disponible")
        receta_bool = datos.get("requiere_receta", None)
        
        # Convertir el booleano en un "Sí" o "No" legible
        requiere_receta = "Sí" if receta_bool else "No" if receta_bool is not None else "No disponible"

        # Formatear la respuesta EXACTAMENTE como se solicita
        respuesta_formateada = f"💊 *{nombre}* — {uso}. ¿Requiere receta? *{requiere_receta}.*"
        
        await update.message.reply_text(respuesta_formateada, parse_mode="Markdown")

    except json.JSONDecodeError as e:
        logging.error(f"Error al parsear JSON: {e}. Respuesta original: {response_text}")
        await update.message.reply_text("No pude procesar la estructura de datos del medicamento de forma correcta.")
    except Exception as e:
        logging.error(f"Error inesperado en buscar_medicamento: {e}\n{traceback.format_exc()}")
        await update.message.reply_text("Lo siento, ocurrió un error al consultar la base de datos médica.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Repite el mensaje del usuario si no es un comando (Función Echo)."""
    await update.message.reply_text(update.message.text)

# --- CONFIGURACIÓN PRINCIPAL ---
def main():
    """Inicia el bot y lo configura con Webhooks."""
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    if not TOKEN or not WEBHOOK_URL:
        logging.error("Error: No se encontraron las variables de entorno TELEGRAM_TOKEN o WEBHOOK_URL.")
        return

    # Crear la aplicación del bot
    application = Application.builder().token(TOKEN).build()

    # Manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("medicamento", buscar_medicamento))

    # Manejador de Eco (Captura todo lo que no sea un comando)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Ejecución por Webhook en el puerto 8000
    logging.info(f"Iniciando Webhook en la URL: {WEBHOOK_URL}/webhook")
    application.run_webhook(
        listen="0.0.0.0",
        port=8000,
        url_path="webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()