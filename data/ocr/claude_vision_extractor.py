import os
import sys
import base64
import json
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

# Añadir ruta de data para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar funciones de almacenamiento y BD
from storage.r2_client import save_image
from database import save_precio, init_db, contar_por_fuente

# Cargar variables de entorno
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path)

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

def encode_image_to_base64(image_bytes):
    """Codifica bytes de imagen a base64."""
    return base64.b64encode(image_bytes).decode('utf-8')

def extract_json_from_image_bytes(image_bytes, media_type="image/png"):
    """
    Extrae JSON de la imagen a partir de sus bytes usando Claude.
    Retorna el diccionario parseado.
    """
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
    # Limpiar backticks si los hay
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    return json.loads(raw_text)

def procesar_carpeta_claude(carpeta="data/imagenes_prueba", guardar=True):
    """
    Procesa todas las imágenes de la carpeta, extrae JSON y guarda en BD.
    Cada imagen se sube a R2 y se guarda la URL en el campo imagen_url.
    Retorna el total de registros guardados.
    """
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
        
        # Leer la imagen en bytes
        try:
            with open(ruta, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            print(f"   ❌ Error al leer imagen: {e}")
            continue
        
        # Detectar media type por extensión
        if archivo.lower().endswith(".png"):
            media_type = "image/png"
        elif archivo.lower().endswith(".jpg") or archivo.lower().endswith(".jpeg"):
            media_type = "image/jpeg"
        else:
            media_type = "image/png"  # fallback
        
        # Extraer JSON con Claude
        try:
            data = extract_json_from_image_bytes(image_bytes, media_type)
        except Exception as e:
            print(f"   ❌ Error al extraer JSON: {e}")
            continue
        
        # --- SUBIR IMAGEN A R2 ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = "ocr_claude"
        # Usar el nombre del archivo sin extensión como base
        base_name = os.path.splitext(archivo)[0]
        filename = f"{base_name}_{timestamp}.png"
        imagen_url = save_image(image_bytes, folder, filename)
        print(f"   📸 Imagen subida: {imagen_url}")
        
        farmacia = data.get('farmacia', 'Farmacia Claude')
        ciudad = data.get('ciudad')
        vigencia = data.get('vigencia')
        medicamentos = data.get('medicamentos', [])
        
        if not medicamentos:
            print("   ⚠️ No se encontraron medicamentos en el JSON.")
            continue
        
        # Guardar cada medicamento
        for med in medicamentos:
            nombre_raw = med.get('nombre', 'desconocido')
            nombre_norm = nombre_raw.lower().strip()
            registro = {
                'medicamento': nombre_norm,
                'nombre_raw': nombre_raw,
                'farmacia': farmacia,
                'ciudad': ciudad,
                'precio': med.get('precio_normal'),
                'precio_promo': med.get('precio_promo'),
                'vigencia': vigencia or med.get('vigencia'),
                'url': None,
                'fuente': 'ocr_claude',
                'fecha': datetime.now().isoformat(),
                'imagen_url': imagen_url   # <--- NUEVO
            }
            if guardar:
                try:
                    save_precio(registro)
                    print(f"   💾 Guardado: {nombre_raw[:30]} - ${registro['precio']}")
                    total_guardados += 1
                except Exception as e:
                    print(f"   ❌ Error al guardar: {e}")
            else:
                # Solo mostrar sin guardar (modo prueba)
                print(f"   📋 {nombre_raw[:30]} - ${registro['precio']}")
                total_guardados += 1
    
    return total_guardados

if __name__ == "__main__":
    init_db()
    print("📦 BD inicializada para Claude")
    
    total = procesar_carpeta_claude("data/imagenes_prueba", guardar=True)
    print(f"\n✅ Total guardados por Claude: {total}")
    
    print("\n📊 Conteo por fuente:")
    try:
        fuente_counts = contar_por_fuente()
        if fuente_counts:
            for fuente, total in fuente_counts.items():
                print(f"  {fuente}: {total}")
        else:
            print("  No hay registros.")
    except Exception as e:
        print(f"Error al contar: {e}")