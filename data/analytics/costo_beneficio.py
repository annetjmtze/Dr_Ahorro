"""
Módulo de análisis de costo‑beneficio para recomendar la mejor opción de compra.
"""

from typing import List, Dict, Any

def calcular_recomendacion(
    farmacias_bd: List[Dict[str, Any]],
    delivery: List[Dict[str, Any]],
    farmacias_mapa: List[str],
    urgente: bool = False
) -> Dict[str, Any]:
    """
    Calcula la recomendación óptima considerando precio, urgencia y conveniencia.

    Args:
        farmacias_bd: Lista de dicts con 'nombre' y 'precio' (float) de la BD.
        delivery: Lista de dicts con 'nombre' y 'precio_total' (float) incluyendo envío.
        farmacias_mapa: Lista de nombres de farmacias que aparecen en el screenshot de Maps.
        urgente: Booleano indicando si el usuario pidió algo urgente.

    Returns:
        Dict con:
            - texto_recomendacion: str, recomendación en lenguaje natural.
            - opcion_ganadora: str, nombre de la opción recomendada.
            - ahorro_vs_delivery: float, diferencia de precio vs la opción de delivery más barata.
    """

    # --- 1. Validar y convertir precios ---
    def to_float(val):
        try:
            return float(val)
        except:
            return float('inf')

    # Limpiar farmacias
    farmacias = []
    for f in farmacias_bd:
        precio = to_float(f.get('precio'))
        if precio != float('inf'):
            farmacias.append({'nombre': f.get('nombre', ''), 'precio': precio})

    # Limpiar delivery
    delivery_opts = []
    for d in delivery:
        precio = to_float(d.get('precio_total'))
        if precio != float('inf'):
            delivery_opts.append({'nombre': d.get('nombre', ''), 'precio_total': precio})

    # --- 2. Identificar opciones clave ---
    farmacia_mas_barata = min(farmacias, key=lambda x: x['precio']) if farmacias else None
    farmacias_en_mapa = [f for f in farmacias if f['nombre'] in farmacias_mapa]
    farmacia_mapa_barata = min(farmacias_en_mapa, key=lambda x: x['precio']) if farmacias_en_mapa else None
    delivery_mas_barato = min(delivery_opts, key=lambda x: x['precio_total']) if delivery_opts else None

    # --- 3. Funciones auxiliares ---
    def get_precio(opcion):
        if opcion is None:
            return float('inf')
        return opcion.get('precio', opcion.get('precio_total', float('inf')))

    def get_nombre(opcion):
        return opcion.get('nombre', 'Opción desconocida') if opcion else None

    # --- 4. Lógica de decisión ---
    opcion_ganadora = None
    razon = ""

    # Caso urgente
    if urgente:
        if delivery_mas_barato:
            opcion_ganadora = delivery_mas_barato
            razon = "Tu consulta indica urgencia, por lo que te recomendamos pedir por delivery para recibirlo lo antes posible."
        else:
            opcion_ganadora = farmacia_mas_barata or farmacia_mapa_barata
            razon = "No encontramos opciones de delivery disponibles. Te sugerimos la farmacia más cercana o económica."
    else:
        # Caso no urgente
        if farmacia_mapa_barata and farmacia_mas_barata:
            diff_mapa_vs_global = abs(farmacia_mapa_barata['precio'] - farmacia_mas_barata['precio'])
            if diff_mapa_vs_global < 15:
                opcion_ganadora = farmacia_mapa_barata
                razon = f"La farmacia más barata ({farmacia_mas_barata['nombre']}) cuesta ${farmacia_mas_barata['precio']:.2f}, pero la farmacia en tu mapa ({farmacia_mapa_barata['nombre']}) cuesta solo ${farmacia_mapa_barata['precio']:.2f}. La diferencia es de ${diff_mapa_vs_global:.2f}, menor a $15, así que te conviene más la del mapa por cercanía."
            else:
                opcion_ganadora = farmacia_mas_barata
                razon = f"La farmacia más barata es {farmacia_mas_barata['nombre']} con ${farmacia_mas_barata['precio']:.2f}, que es ${farmacia_mas_barata['precio'] - farmacia_mapa_barata['precio']:.2f} más barata que la del mapa. Vale la pena el traslado."
        elif farmacia_mapa_barata:
            opcion_ganadora = farmacia_mapa_barata
            razon = "La única farmacia cercana en tu mapa es la mejor opción."
        elif farmacia_mas_barata:
            opcion_ganadora = farmacia_mas_barata
            razon = "No encontramos farmacias en tu mapa, pero la más barata de nuestra base de datos es..."
        else:
            opcion_ganadora = delivery_mas_barato
            razon = "No hay farmacias disponibles en la base de datos. Te sugerimos pedir por delivery."

        # --- Comparar con delivery si existe ---
        if delivery_mas_barato and opcion_ganadora and 'precio' in opcion_ganadora:
            diff_farmacia_vs_delivery = abs(opcion_ganadora['precio'] - delivery_mas_barato['precio_total'])
            if diff_farmacia_vs_delivery < 15:
                # Si la farmacia no está en el mapa, recomendar delivery
                if opcion_ganadora['nombre'] not in farmacias_mapa:
                    opcion_ganadora = delivery_mas_barato
                    razon = f"La farmacia más barata cuesta ${farmacia_mas_barata['precio']:.2f} pero el delivery solo cuesta ${delivery_mas_barato['precio_total']:.2f} (incluye envío). La diferencia es de ${diff_farmacia_vs_delivery:.2f}, menor a $15, por lo que te conviene más pedir por delivery."
                # Si está en el mapa, mantenerla (ya es cómoda)

        # Si no hay opción ganadora aún, usar delivery
        if not opcion_ganadora and delivery_mas_barato:
            opcion_ganadora = delivery_mas_barato
            razon = "Te recomendamos la opción de delivery más económica."

    # --- 5. Calcular ahorro vs delivery ---
    precio_delivery_base = delivery_mas_barato['precio_total'] if delivery_mas_barato else None
    if opcion_ganadora and precio_delivery_base is not None:
        if 'precio' in opcion_ganadora:
            ahorro = opcion_ganadora['precio'] - precio_delivery_base
        else:
            ahorro = opcion_ganadora['precio_total'] - precio_delivery_base
    else:
        ahorro = 0.0

    # --- 6. Construir texto de recomendación ---
    if opcion_ganadora:
        nombre = opcion_ganadora.get('nombre', 'Opción desconocida')
        if 'precio' in opcion_ganadora:
            precio_text = f"${opcion_ganadora['precio']:.2f}"
        else:
            precio_text = f"${opcion_ganadora['precio_total']:.2f} (incluye envío)"
        texto = f"💡 *Recomendación:* {razon} Por lo tanto, te sugerimos *{nombre}* por un costo de {precio_text}."
    else:
        texto = "💡 *Recomendación:* No pudimos encontrar opciones disponibles. Intenta de nuevo más tarde."

    return {
        'texto_recomendacion': texto,
        'opcion_ganadora': opcion_ganadora['nombre'] if opcion_ganadora else None,
        'ahorro_vs_delivery': ahorro
    }