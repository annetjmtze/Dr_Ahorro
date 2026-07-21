import asyncio
import datetime
from data.agents.rappi_agent import RappiAgent
from data.agents.ubereats_agent import UberEatsAgent

async def main():
    # Lista de medicamentos (máximo 15-20 por sesión, pero aquí usamos 4 en total)
    medicamentos = ["paracetamol 500mg", "ibuprofeno 400mg", "omeprazol 20mg"]
    # Para Uber Eats solo necesitamos 1
    medicamento_ue = ["paracetamol 500mg"]

    # Crear agentes (headless=False para ver el navegador, opcional)
    rappi = RappiAgent(headless=False)
    ubereats = UberEatsAgent(headless=False)

    print("🔍 Probando Rappi...")
    resultados_rappi = []
    for med in medicamentos:
        res = await rappi.search_medication(med)
        resultados_rappi.append(res)
        if res:
            print(f"✅ Rappi - {med}: ${res['precio']} en {res['farmacia']}")
            print(f"   Link: {res['link_producto']}")
        else:
            print(f"❌ Rappi - {med}: falló")

    print("\n🔍 Probando Uber Eats...")
    for med in medicamento_ue:
        res = await ubereats.search_medication(med)
        if res:
            print(f"✅ Uber Eats - {med}: ${res['precio']} en {res['farmacia']}")
            print(f"   Link: {res['link_producto']}")
        else:
            print(f"❌ Uber Eats - {med}: falló")

    # Resumen
    print("\n📊 Resumen:")
    print(f"Rappi: {sum(1 for r in resultados_rappi if r)} de {len(medicamentos)} éxitos")
    # (Uber Eats solo 1)

if __name__ == "__main__":
    asyncio.run(main())