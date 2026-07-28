import os
import json
import logging
from datetime import datetime
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

    def normalizar(self, nombre_medicamento: str, hora_actual: int = None) -> dict:
        """
        Normaliza el nombre del medicamento y detecta urgencia.
        :param nombre_medicamento: texto del usuario.
        :param hora_actual: hora (0-23) opcional para pruebas; si no se da, usa datetime.now().hour.
        :return: dict con campos: nombre_ingresado, nombre_generico, uso_principal,
                 requiere_receta, urgente (bool), y opcionalmente 'error'.
        """
        if not self.client:
            return {"error": "Cliente de Anthropic no inicializado", "urgente": False}

        if hora_actual is None:
            hora_actual = datetime.now().hour

        # Determinar si es de noche (10pm a 6am)
        es_de_noche = hora_actual >= 22 or hora_actual < 6

        try:
            system_prompt = f"""Eres un asistente experto en medicamentos en México.
            Tu respuesta DEBE ser únicamente un objeto JSON válido, sin texto adicional.
            El JSON debe tener estos campos:
            {{
                "nombre_ingresado": "string",
                "nombre_generico": "string",
                "uso_principal": "string",
                "requiere_receta": boolean,
                "urgente": boolean
            }}
            Para el campo "urgente", debes decidir si el usuario expresa urgencia.
            Señales de urgencia:
            - Palabras como: "urgente", "ahorita", "ya", "necesito ahora", "es de noche", "no puedo esperar".
            - También considera que actualmente son las {hora_actual} horas. Si está entre 22:00 y 6:00, es probable que el usuario necesite el medicamento con urgencia (farmcias cerradas).
            Si el mensaje no contiene indicios, asigna false.
            """

            message = self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=300,
                system=system_prompt,
                messages=[{"role": "user", "content": nombre_medicamento}]
            )
            response_text = message.content[0].text.strip()
            # Limpiar posibles marcadores
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            data = json.loads(response_text)
            # Asegurar que el campo urgente existe
            if "urgente" not in data:
                data["urgente"] = False
            return data

        except anthropic.RateLimitError as e:
            logging.warning(f"Rate limit alcanzado en Anthropic: {e}")
            return {"error": "Alcanzamos el límite de consultas por hoy. Vuelve mañana.", "urgente": False}
        except Exception as e:
            logging.error(f"Error en normalizer: {e}")
            return {"error": str(e), "urgente": False}