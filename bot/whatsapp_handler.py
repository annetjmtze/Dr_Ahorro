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
    # Farmacia más barata de toda la BD
    farmacia_mas_barata = min(farmacias, key=lambda x: x['precio']) if farmacias else None

    # Farmacia más barata entre las que están en el mapa
    farmacias_en_mapa = [f for f in farmacias if f['nombre'] in farmacias_mapa]
    farmacia_mapa_barata = min(farmacias_en_mapa, key=lambda x: x['precio']) if farmacias_en_mapa else None

    # Delivery más barato
    delivery_mas_barato = min(delivery_opts, key=lambda x: x['precio_total']) if delivery_opts else None

    # --- 3. Lógica de decisión ---
    opcion_ganadora = None
    razon = ""

    # Caso urgente: priorizar delivery siempre
    if urgente:
        if delivery_mas_barato:
            opcion_ganadora = delivery_mas_barato
            razon = "Tu consulta indica urgencia, por lo que te recomendamos pedir por delivery para recibirlo lo antes posible."
        else:
            # Si no hay delivery, caer en la farmacia más barata
            opcion_ganadora = farmacia_mas_barata or farmacia_mapa_barata
            razon = "No encontramos opciones de delivery disponibles. Te sugerimos la farmacia más cercana o económica."
    else:
        # Caso no urgente
        if farmacia_mapa_barata and farmacia_mas_barata:
            # Comparar la farmacia del mapa con la más barata global
            diff_mapa_vs_global = abs(farmacia_mapa_barata['precio'] - farmacia_mas_barata['precio'])
            if diff_mapa_vs_global < 15:
                # La diferencia es pequeña, recomendar la del mapa (más conveniente)
                opcion_ganadora = farmacia_mapa_barata
                razon = f"La farmacia más barata ({farmacia_mas_barata['nombre']}) cuesta ${farmacia_mas_barata['precio']:.2f}, pero la farmacia en tu mapa ({farmacia_mapa_barata['nombre']}) cuesta solo ${farmacia_mapa_barata['precio']:.2f}. La diferencia es de ${diff_mapa_vs_global:.2f}, menor a $15, así que te conviene más la del mapa por cercanía."
            else:
                # Diferencia significativa, elegir la más barata global
                opcion_ganadora = farmacia_mas_barata
                razon = f"La farmacia más barata es {farmacia_mas_barata['nombre']} con ${farmacia_mas_barata['precio']:.2f}, que es ${farmacia_mas_barata['precio'] - farmacia_mapa_barata['precio']:.2f} más barata que la del mapa. Vale la pena el traslado."
        elif farmacia_mapa_barata:
            # Solo hay farmacia en el mapa
            opcion_ganadora = farmacia_mapa_barata
            razon = "La única farmacia cercana en tu mapa es la mejor opción."
        elif farmacia_mas_barata:
            # No hay farmacia en el mapa, usar la más barata global
            opcion_ganadora = farmacia_mas_barata
            razon = "No encontramos farmacias en tu mapa, pero la más barata de nuestra base de datos es..."
        else:
            # No hay farmacias, caer en delivery si existe
            opcion_ganadora = delivery_mas_barato
            razon = "No hay farmacias disponibles en la base de datos. Te sugerimos pedir por delivery."

        # Comparar con delivery (si existe) para ver si es mejor
        if delivery_mas_barato and opcion_ganadora:
            # Si la opción actual es una farmacia, comparar con delivery
            if 'precio' in opcion_ganadora:  # es farmacia
                diff_farmacia_vs_delivery = abs(opcion_ganadora['precio'] - delivery_mas_barato['precio_total'])
                if diff_farmacia_vs_delivery < 15:
                    # Diferencia pequeña: delivery es más cómodo, pero si la farmacia está en el mapa, ya es cómoda.
                    # Decidir: si la farmacia está en el mapa, mantenerla; si no, cambiar a delivery.
                    if opcion_ganadora['nombre'] in farmacias_mapa:
                        # Ya es del mapa, mantener
                        pass
                    else:
                        # Si no está en el mapa y la diferencia es pequeña, delivery es mejor (no salir)
                        opcion_ganadora = delivery_mas_barato
                        razon = f"La farmacia más barata cuesta ${opcion_ganadora['precio']:.2f} pero el delivery solo cuesta ${delivery_mas_barato['precio_total']:.2f} (incluye envío). La diferencia es de ${diff_farmacia_vs_delivery:.2f}, menor a $15, por lo que te conviene más pedir por delivery."
                # Si la diferencia es grande, mantener la farmacia (ya elegida)
            # Si la opción ya es delivery, no hacemos nada

        # Si no hay opción ganadora aún, usar delivery
        if not opcion_ganadora and delivery_mas_barato:
            opcion_ganadora = delivery_mas_barato
            razon = "Te recomendamos la opción de delivery más económica."

    # --- 4. Calcular ahorro vs delivery ---
    # Precio del delivery más barato (para comparar)
    precio_delivery_base = delivery_mas_barato['precio_total'] if delivery_mas_barato else float('inf')
    if opcion_ganadora:
        if 'precio' in opcion_ganadora:  # es farmacia
            ahorro = opcion_ganadora['precio'] - precio_delivery_base
        else:  # es delivery
            ahorro = 0.0  # comparado consigo mismo
    else:
        ahorro = 0.0

    # --- 5. Construir texto de recomendación ---
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