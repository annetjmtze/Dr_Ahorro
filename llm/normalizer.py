import os
import json
import logging
import anthropic
from dotenv import load_dotenv

load_dotenv()

class MedicamentoNormalizer:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logging.warning("ANTHROPIC_API_KEY no encontrada")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def normalizar(self, nombre_medicamento: str) -> dict:
        if not self.client:
            return {"error": "Cliente de Anthropic no inicializado"}
        
        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=300,
                system="""Eres un asistente experto en medicamentos en México. 
                Da una descripción breve. Tu respuesta DEBE ser únicamente un 
                objeto JSON válido, sin texto adicional. 
                El JSON debe tener:
                {
                    "nombre_ingresado": "string",
                    "nombre_generico": "string",
                    "uso_principal": "string",
                    "requiere_receta": boolean
                }""",
                messages=[{"role": "user", "content": nombre_medicamento}]
            )
            response_text = message.content[0].text.strip()
            # Limpiar posibles marcadores
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            return json.loads(response_text)
        except Exception as e:
            logging.error(f"Error en normalizer: {e}")
            return {"error": str(e)}