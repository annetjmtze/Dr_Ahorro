# data/verificar_bd.py
import sys
import os

# Asegura que el directorio 'data' esté en el path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, contar_por_fuente, get_resumen

def main():
    init_db()  # asegura que la tabla exista

    print("\n" + "="*50)
    print("📊 VERIFICACIÓN DE BASE DE DATOS")
    print("="*50)

    # 1. Conteo por fuente
    print("\n📌 REGISTROS POR FUENTE:")
    total = 0
    for row in contar_por_fuente():
        print(f"   {row['fuente']}: {row['total']}")
        total += row['total']
    print(f"   TOTAL: {total}")

    # 2. Mostrar algunos resúmenes de medicamentos
    medicamentos_ejemplo = ["paracetamol", "ibuprofeno", "desconocido"]
    print("\n📌 RESUMEN DE PRECIOS (últimas 24h, ordenados menor a mayor):")
    for med in medicamentos_ejemplo:
        resultados = get_resumen(med)
        if resultados:
            print(f"\n   💊 {med.upper()}:")
            for r in resultados[:5]:  # mostrar hasta 5
                print(f"      - {r['farmacia']}: ${r['precio']} (fuente: {r['fuente']})")
        else:
            print(f"\n   💊 {med.upper()}: sin registros en últimas 24h")

    # 3. Verificar si hay al menos 20 registros totales y más de una fuente
    print("\n" + "="*50)
    if total >= 20:
        print("✅ ¡Felicidades! Tienes 20 o más registros.")
    else:
        print(f"⚠️ Solo tienes {total} registros. Necesitas al menos 20.")
    
    fuentes = [row['fuente'] for row in contar_por_fuente()]
    if len(fuentes) >= 2:
        print(f"✅ Tienes registros de {len(fuentes)} fuentes distintas: {', '.join(fuentes)}")
    else:
        print(f"⚠️ Solo tienes una fuente: {fuentes[0] if fuentes else 'ninguna'}. Debes tener al menos 2.")

if __name__ == "__main__":
    main()