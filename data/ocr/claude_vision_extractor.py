import os
import base64
import json
from anthropic import Anthropic
from dotenv import load_dotenv
import os

# Construye la ruta al .env desde la raíz del proyecto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path)

# Carga tu API key desde variable de entorno
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY no está configurada")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Eres extractor de precios de medicamentos en México.
Analiza la imagen. Devuelve ÚNICAMENTE JSON válido.
Sin texto adicional. Sin backticks.
{
  "farmacia": "nombre o null",
  "ciudad": "ciudad o null",
  "vigencia": "YYYY-MM-DD o null",
  "medicamentos": [
    {
      "nombre": "exacto como aparece",
      "precio_normal": 0.0,
      "precio_promo": 0.0 o null,
      "unidad": "tab/ml/g o null"
    }
  ]
}"""

def encode_image_to_base64(image_path):
    """Convierte una imagen a base64 para enviarla a Claude."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_json_from_image(image_path):
    """
    Envía la imagen a Claude Vision y devuelve el JSON estructurado.
    """
    media_type = "image/jpeg"
    if image_path.lower().endswith(".png"):
        media_type = "image/png"
    elif image_path.lower().endswith(".gif"):
        media_type = "image/gif"
    elif image_path.lower().endswith(".webp"):
        media_type = "image/webp"

    base64_image = encode_image_to_base64(image_path)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",  # o claude-3-opus-20240229
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extrae los precios y medicamentos de esta imagen."
                    }
                ]
            }
        ]
    )

    # Claude devuelve el texto; lo parseamos como JSON
    raw_text = response.content[0].text.strip()
    # Si por alguna razón vienen backticks, los removemos
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    return json.loads(raw_text)

# Ejemplo de uso directo
if __name__ == "__main__":
    test_image = "data/imagenes_prueba/farmacia_1.jpg"
    if os.path.exists(test_image):
        resultado = extract_json_from_image(test_image)
        print("=== JSON EXTRAÍDO POR CLAUDE VISION ===\n")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        print(f"No se encontró la imagen: {test_image}")