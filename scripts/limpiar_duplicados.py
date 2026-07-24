#!/usr/bin/env python3
import os
import sys
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL no configurada")
    sys.exit(1)

def main():
    print("🔍 Conectando a la base de datos...")
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()

    print("🔍 Identificando duplicados (agrupando por medicamento, farmacia y fecha sin hora)...")
    cur.execute("""
        SELECT id
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY medicamento, farmacia, SPLIT_PART(fecha, 'T', 1)
                       ORDER BY id DESC
                   ) AS rn
            FROM precios
        ) t
        WHERE rn > 1
    """)
    rows = cur.fetchall()

    if not rows:
        print("✅ No hay duplicados")
        conn.close()
        return

    ids = [row["id"] for row in rows]
    print(f"🔍 Se encontraron {len(ids)} duplicados para eliminar")

    # Eliminar en lotes de 100
    batch_size = 100
    total_eliminados = 0
    total_lotes = (len(ids) + batch_size - 1) // batch_size

    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        placeholders = ",".join(["%s"] * len(batch))
        cur.execute(f"DELETE FROM precios WHERE id IN ({placeholders})", batch)
        eliminados = cur.rowcount
        total_eliminados += eliminados
        conn.commit()
        lote_actual = i // batch_size + 1
        print(f"   ✅ Lote {lote_actual}/{total_lotes}: eliminados {eliminados} registros")

    print(f"✅ Total eliminados: {total_eliminados}")

    # Verificar que no queden duplicados
    cur.execute("""
        SELECT farmacia, medicamento, COUNT(*) as duplicados
        FROM precios
        WHERE medicamento = 'paracetamol'
        GROUP BY farmacia, medicamento
        HAVING COUNT(*) > 1
    """)
    restantes = cur.fetchall()
    if restantes:
        print("⚠️ Aún quedan duplicados:")
        for row in restantes:
            print(f"   {row['farmacia']}: {row['duplicados']}")
    else:
        print("✅ Todos los duplicados han sido eliminados.")

    conn.close()

if __name__ == "__main__":
    main()