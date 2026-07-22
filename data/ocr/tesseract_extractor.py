# data/ocr/tesseract_extractor.py
import os
import re
from datetime import datetime
from PIL import Image, ImageEnhance
import pytesseract

# Añadir ruta de data para importar módulos
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.r2_client import save_image
from database import save_precio, init_db, contar_por_fuente

# Configurar ruta de Tesseract (ajústala si es necesario)
# En Railway/Linux, normalmente está en /usr/bin/tesseract
if sys.platform == "win32":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # En Linux, suele estar en el PATH, pero podemos forzar si es necesario
    # pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    pass

def preprocess(image_path):
    """Mejora el contraste de la imagen para OCR."""
    img = Image.open(image_path).convert('L')
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(2.0)

def extract_text(image_path):
    """Extrae texto de la imagen usando Tesseract."""
    processed_img = preprocess(image_path)
    text = pytesseract.image_to_string(processed_img, lang='spa')
    return text.strip()

def parsear_texto_a_precios(texto, farmacia_default="Farmacia OCR", imagen_url=None):
    """
    Intenta extraer pares (medicamento, precio) del texto OCR.
    Retorna una lista de diccionarios listos para guardar, incluyendo imagen_url.
    """
    lineas = texto.split('\n')
    resultados = []
    # Patrón para precios: números con coma o punto, dos decimales opcionales
    patron_precio = r'(\d+[.,]\d{2})'
    # También buscar precios sin decimales (ej. "$50")
    patron_precio_sin_dec = r'(\d+)'
    
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
        # Buscar precio en la línea
        precios = re.findall(patron_precio, linea)
        if not precios:
            # Si no encuentra con decimales, buscar sin decimales
            precios = re.findall(patron_precio_sin_dec, linea)
        if precios:
            # Tomar el primer precio encontrado
            precio_str = precios[0].replace(',', '.')
            try:
                precio = float(precio_str)
            except ValueError:
                continue
            # El resto de la línea es el nombre del medicamento (quitar el precio)
            nombre = re.sub(r'[$]?\s*' + re.escape(precios[0]), '', linea).strip()
            # Limpiar caracteres extraños
            nombre = re.sub(r'[^a-zA-ZáéíóúñÑ0-9\s]', '', nombre).strip()
            if not nombre or len(nombre) < 3:
                nombre = "medicamento_desconocido"
            # Normalizar el nombre (tomar primera palabra como medicamento)
            medicamento = nombre.split()[0].lower() if nombre else "desconocido"
            resultados.append({
                'medicamento': medicamento,
                'nombre_raw': nombre,
                'farmacia': farmacia_default,
                'ciudad': None,
                'precio': precio,
                'precio_promo': None,
                'vigencia': None,
                'url': None,
                'fuente': 'ocr_tesseract',
                'fecha': datetime.now().isoformat(),
                'imagen_url': imagen_url   # <--- NUEVO
            })
    return resultados

def procesar_y_guardar(image_path, farmacia="Farmacia OCR"):
    """
    Extrae texto de la imagen, sube la imagen a R2, parsea precios y guarda en BD.
    Retorna la lista de registros guardados.
    """
    # --- LEER LA IMAGEN Y SUBIR A R2 ---
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    except Exception as e:
        print(f"⚠️ Error al leer imagen {image_path}: {e}")
        return []
    
    # Subir a R2
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = "ocr_tesseract"
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    filename = f"{base_name}_{timestamp}.png"
    imagen_url = save_image(image_bytes, folder, filename)
    print(f"   📸 Imagen subida: {imagen_url}")
    
    # Extraer texto con Tesseract
    texto = extract_text(image_path)
    if not texto:
        print(f"⚠️ No se pudo extraer texto de {image_path}")
        return []
    
    registros = parsear_texto_a_precios(texto, farmacia, imagen_url)
    for r in registros:
        try:
            save_precio(r)
            print(f"💾 Guardado Tesseract: {r['nombre_raw']} - ${r['precio']}")
        except Exception as e:
            print(f"⚠️ Error guardando: {e}")
    return registros

if __name__ == "__main__":
    # Inicializar BD
    init_db()
    print("📦 Base de datos inicializada para Tesseract")
    
    # Ruta a las imágenes de prueba
    carpeta_imagenes = "data/imagenes_prueba"
    imagenes = []
    if os.path.exists(carpeta_imagenes):
        imagenes = [os.path.join(carpeta_imagenes, f) for f in os.listdir(carpeta_imagenes) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    else:
        print(f"⚠️ Carpeta {carpeta_imagenes} no encontrada. Usando imagen específica.")
        test_image = "data/imagenes_prueba/farmacia_1.jpg"
        if os.path.exists(test_image):
            imagenes = [test_image]
    
    if not imagenes:
        print("❌ No se encontraron imágenes para procesar.")
        exit()
    
    total_guardados = 0
    for img in imagenes:
        print(f"\n🔍 Procesando {img}...")
        registros = procesar_y_guardar(img, farmacia="Farmacia Tesseract")
        total_guardados += len(registros)
        print(f"   ✅ Extraídos {len(registros)} precios")
    
    print(f"\n📊 Total registros guardados por Tesseract: {total_guardados}")
    
    # Mostrar conteo por fuente
    print("\n📊 Registros en BD por fuente:")
    try:
        fuente_counts = contar_por_fuente()
        if fuente_counts:
            for fuente, total in fuente_counts.items():
                print(f"  {fuente}: {total}")
        else:
            print("  No hay registros.")
    except Exception as e:
        print(f"Error al contar: {e}")