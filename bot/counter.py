import os
import json
import logging
from datetime import datetime

COUNTER_FILE = "daily_counter.json"
LIMITE_DIARIO = 10             # Límite del sandbox de Twilio
LIMITE_NOTIFICACION = int(LIMITE_DIARIO * 0.8)  # 80% = 8

def _get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def _load_counter():
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                return json.load(f)
        except:
            return {"date": _get_today_str(), "count": 0, "notified": False}
    return {"date": _get_today_str(), "count": 0, "notified": False}

def _save_counter(data):
    with open(COUNTER_FILE, "w") as f:
        json.dump(data, f)

def increment_and_check_limit() -> bool:
    """
    Incrementa el contador de mensajes del día.
    Retorna True si se alcanzó el 80% y no se había notificado antes.
    """
    today = _get_today_str()
    data = _load_counter()

    if data["date"] != today:
        data = {"date": today, "count": 0, "notified": False}

    data["count"] += 1
    should_notify = False

    if data["count"] >= LIMITE_NOTIFICACION and not data["notified"]:
        should_notify = True
        data["notified"] = True

    _save_counter(data)
    return should_notify

# ---------- NUEVAS FUNCIONES ----------
def is_limit_reached() -> bool:
    """
    Retorna True si ya se alcanzó el límite diario (sin incrementar).
    """
    today = _get_today_str()
    data = _load_counter()
    if data["date"] != today:
        return False
    return data["count"] >= LIMITE_DIARIO

def get_remaining() -> int:
    """
    Retorna cuántos mensajes quedan disponibles hoy.
    """
    today = _get_today_str()
    data = _load_counter()
    if data["date"] != today:
        return LIMITE_DIARIO
    remaining = LIMITE_DIARIO - data["count"]
    return remaining if remaining > 0 else 0

# Exportar constantes y funciones
__all__ = ['increment_and_check_limit', 'is_limit_reached', 'get_remaining', 
           'LIMITE_DIARIO', 'LIMITE_NOTIFICACION']