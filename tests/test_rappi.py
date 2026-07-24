#!/usr/bin/env python3
"""
Prueba local del agente de Rappi.
Ejecutar con: python test_rappi.py
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar el agente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.agents.rappi_agent import RappiAgent

async def main():
    print("🔍 Iniciando prueba del agente de Rappi...")
    
    # Crear instancia con headless=False para ver el navegador
    agent = RappiAgent(headless=False)
    
    # Medicamento a buscar (cambia por el que quieras probar)
    medicamento = "paracetamol"
    print(f"🔎 Buscando: {medicamento}")
    
    # Ejecutar búsqueda
    resultado = await agent.search_medication(medicamento)
    
    if resultado:
        print("\n✅ Resultado obtenido:")
        print(f"   - Farmacia: {resultado.get('farmacia')}")
        print(f"   - Precio: ${resultado.get('precio')}")
        print(f"   - Link web: {resultado.get('link_producto')}")
        print(f"   - Deep link (app): {resultado.get('deep_link')}")
        print(f"   - ID del producto: {resultado.get('product_id')}")
        print(f"   - Captura guardada en: {resultado.get('imagen_url')}")
    else:
        print("❌ No se obtuvo ningún resultado.")

if __name__ == "__main__":
    asyncio.run(main())