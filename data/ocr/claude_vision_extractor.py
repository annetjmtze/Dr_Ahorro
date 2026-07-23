import os
import sys
import base64
import json
from datetime import datetime

# ── 1. Definir ROOT_DIR y cargar .env ANTES de importar módulos del proyecto ──
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, '.env'))

# ── 2. AHORA importar módulos del proyecto (ya tienen USE_R2 cargada) ──
from data.storage.r2_client import save_image
from data.database import save_precio, init_db, contar_por_fuente

from anthropic import Anthropic

# ── 3. Resto del código (sin cambios) ──
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("❌ ANTHROPIC_API_KEY no está configurada")

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

def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def extract_json_from_image_bytes(image_bytes, media_type="image/png"):
    base64_image = encode_image_to_base64(image_bytes)
    response = client.messages.create(
        model="claude-haiku-4-5",
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
    raw_text = response.content[0].text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    return json.loads(raw_text)

def procesar_carpeta_claude(carpeta="data/imagenes_prueba", guardar=True):
    total_guardados = 0
    if not os.path.exists(carpeta):
        print(f"⚠️ Carpeta {carpeta} no existe.")
        return 0

    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not archivos:
        print("⚠️ No hay imágenes en la carpeta.")
        return 0

    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        print(f"\n🔍 Procesando con Claude: {archivo}...")

        try:
            with open(ruta, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            print(f"   ❌ Error al leer imagen: {e}")
            continue

        media_type = "image/png" if archivo.lower().endswith(".png") else "image/jpeg"

        try:
            data = extract_json_from_image_bytes(image_bytes, media_type)
        except Exception as e:
            print(f"   ❌ Error al extraer JSON: {e}")
            continue

        # Subir imagen a R2 (ahora USE_R2 será true)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = "ocr_claude"
        base_name = os.path.splitext(archivo)[0]
        filename = f"{base_name}_{timestamp}.png"
        imagen_url = save_image(image_bytes, folder, filename)
        print(f"   📸 Imagen guardada: {imagen_url}")

        farmacia = data.get('farmacia', 'Farmacia Claude')
        ciudad = data.get('ciudad')
        vigencia = data.get('vigencia')
        medicamentos = data.get('medicamentos', [])

        if not medicamentos:
            print("   ⚠️ No se encontraron medicamentos en el JSON.")
            continue

        for med in medicamentos:
            nombre_raw = med.get('nombre', 'desconocido')
            nombre_norm = nombre_raw.lower().strip()
            precio = med.get('precio_normal')
            if precio is None:
                print(f"   ⚠️ Sin precio para {nombre_raw}, omitiendo")
                continue
            registro = {
                'medicamento': nombre_norm,
                'nombre_raw': nombre_raw,
                'farmacia': farmacia,
                'ciudad': ciudad,
                'precio': precio,
                'precio_promo': med.get('precio_promo'),
                'vigencia': vigencia or med.get('vigencia'),
                'url': None,
                'fuente': 'ocr_claude',
                'fecha': datetime.now().isoformat(),
                'imagen_url': imagen_url
            }
            if guardar:
                try:
                    save_precio(registro)
                    print(f"   💾 Guardado: {nombre_raw[:30]} - ${registro['precio']}")
                    total_guardados += 1
                except Exception as e:
                    print(f"   ❌ Error al guardar: {e}")
            else:
                print(f"   📋 {nombre_raw[:30]} - ${registro['precio']}")

    return total_guardados

if __name__ == "__main__":
    init_db()
    print("📦 BD inicializada para Claude")
    total = procesar_carpeta_claude("data/imagenes_prueba", guardar=True)
    print(f"\n✅ Total guardados por Claude: {total}")
    try:
        fuente_counts = contar_por_fuente()
        if fuente_counts:
            print("\n📊 Conteo por fuente:")
            for fuente, total in fuente_counts.items():
                print(f"  {fuente}: {total}")
        else:
            print("  No hay registros.")
    except Exception as e:
        print(f"Error al contar: {e}")