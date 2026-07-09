from PIL import Image, ImageEnhance
import pytesseract
import os

# 🔥 Fuerza la ruta de Tesseract (por si no está en el PATH)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess(path):
    img = Image.open(path).convert('L')
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(2.0)

def extract_text(path):
    processed_img = preprocess(path)
    text = pytesseract.image_to_string(processed_img, lang='spa')
    return text.strip()

if __name__ == "__main__":
    test_image = "data/imagenes_prueba/farmacia_1.jpg"
    if os.path.exists(test_image):
        resultado = extract_text(test_image)
        print("=== TEXTO EXTRAÍDO POR TESSERACT ===\n")
        print(resultado)
    else:
        print(f"No se encontró la imagen: {test_image}")