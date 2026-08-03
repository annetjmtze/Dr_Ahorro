import asyncio
import logging
import sys
import os

# Asegurar que el path sea correcto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.agents.ubereats_agent import UberEatsAgent

logging.basicConfig(level=logging.INFO)

async def test():
    # headless=False para ver el navegador (útil para depurar)
    agent = UberEatsAgent(headless=False)
    print("🔍 Buscando 'paracetamol' en Uber Eats...")
    resultado = await agent.search_medication("paracetamol")
    if resultado:
        print("\n✅ Resultado obtenido:")
        print(f"  - Medicamento: {resultado.get('medicamento')}")
        print(f"  - Farmacia: {resultado.get('farmacia')}")
        print(f"  - Precio: ${resultado.get('precio')}")
        print(f"  - Link: {resultado.get('link_producto')}")
        print(f"  - Entrega: {resultado.get('entrega_estimada')}")
    else:
        print("\n❌ No se encontraron resultados o hubo un error.")

if __name__ == "__main__":
    asyncio.run(test())
    