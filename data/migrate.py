"""
Script de migración: SQLite → PostgreSQL (versión robusta)
Ejecutar: python data/migrate.py
"""
import sqlite3
import psycopg
import os
from datetime import datetime
import sys

SQLITE_PATH = "data/precios.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

def migrar():
    print("=" * 70)
    print("🚀 MIGRACIÓN SQLite → PostgreSQL (modo robusto)")
    print(f"📁 SQLite: {SQLITE_PATH}")
    print(f"🐘 PostgreSQL: {'Configurada' if POSTGRES_URL else '❌ NO CONFIGURADA'}")
    print("=" * 70)

    if not POSTGRES_URL:
        print("❌ Error: DATABASE_URL no está configurada como variable de entorno")
        print("   Exportala con: $env:DATABASE_URL='postgresql://...'")
        return

    # 1. Conectar a SQLite
    print("\n📂 Conectando a SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # 2. Contar registros en SQLite
    sqlite_cursor.execute("SELECT COUNT(*) FROM precios")
    count_sqlite = sqlite_cursor.fetchone()[0]
    print(f"   Registros en SQLite: {count_sqlite}")

    if count_sqlite == 0:
        print("⚠️  No hay registros para migrar. Saliendo...")
        sqlite_conn.close()
        return

    # 3. Leer todos los datos de SQLite (evitamos múltiples consultas)
    print("\n📖 Leyendo todos los datos de SQLite...")
    sqlite_cursor.execute("""
        SELECT medicamento, nombre_raw, farmacia, ciudad, precio, precio_promo,
               vigencia, url, imagen_url, fuente, fecha
        FROM precios
    """)
    rows = sqlite_cursor.fetchall()
    print(f"   Leídos {len(rows)} registros")
    sqlite_conn.close()

    # 4. Conectar a PostgreSQL
    print("\n🐘 Conectando a PostgreSQL...")
    pg_conn = psycopg.connect(POSTGRES_URL)
    pg_cursor = pg_conn.cursor()

    # 5. Opcional: vaciar tabla (si ya tenía datos) - PREGUNTAR
    pg_cursor.execute("SELECT COUNT(*) FROM precios")
    existing = pg_cursor.fetchone()[0]
    if existing > 0:
        print(f"   ⚠️  La tabla ya tiene {existing} registros. Se van a eliminar antes de migrar.")
        pg_cursor.execute("TRUNCATE TABLE precios RESTART IDENTITY")
        pg_conn.commit()
        print("   ✅ Tabla vaciada.")

    # 6. Migrar en lotes (batch) para mejorar rendimiento
    print("\n💾 Insertando en PostgreSQL (lotes de 100)...")
    batch_size = 100
    total_insertados = 0
    errores = 0
    errores_detalle = []

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        print(f"   Procesando lote {i//batch_size + 1} (registros {i+1}-{min(i+batch_size, len(rows))})...")
        
        try:
            # Preparar datos del lote como lista de tuplas
            batch_data = []
            for row in batch:
                # Convertir valores a tipos compatibles
                precio = float(row['precio']) if row['precio'] is not None else None
                precio_promo = float(row['precio_promo']) if row['precio_promo'] is not None else None
                # Los demás campos son texto
                batch_data.append((
                    row['medicamento'],
                    row['nombre_raw'],
                    row['farmacia'],
                    row['ciudad'],
                    precio,
                    precio_promo,
                    row['vigencia'],
                    row['url'],
                    row['imagen_url'],
                    row['fuente'],
                    row['fecha']
                ))
            
            # Insertar el lote completo
            pg_cursor.executemany("""
                INSERT INTO precios (
                    medicamento, nombre_raw, farmacia, ciudad, precio, precio_promo,
                    vigencia, url, imagen_url, fuente, fecha
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch_data)
            pg_conn.commit()
            total_insertados += len(batch)
            print(f"      ✅ Lote insertado correctamente ({len(batch)} registros)")

        except Exception as e:
            # Si falla el lote, hacemos rollback y procesamos registro por registro para identificar errores
            pg_conn.rollback()
            print(f"      ❌ Error en lote: {e}")
            print(f"      🔍 Intentando inserción individual...")

            for row in batch:
                try:
                    precio = float(row['precio']) if row['precio'] is not None else None
                    precio_promo = float(row['precio_promo']) if row['precio_promo'] is not None else None
                    pg_cursor.execute("""
                        INSERT INTO precios (
                            medicamento, nombre_raw, farmacia, ciudad, precio, precio_promo,
                            vigencia, url, imagen_url, fuente, fecha
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row['medicamento'],
                        row['nombre_raw'],
                        row['farmacia'],
                        row['ciudad'],
                        precio,
                        precio_promo,
                        row['vigencia'],
                        row['url'],
                        row['imagen_url'],
                        row['fuente'],
                        row['fecha']
                    ))
                    pg_conn.commit()
                    total_insertados += 1
                except Exception as inner_e:
                    pg_conn.rollback()
                    errores += 1
                    errores_detalle.append(f"Registro {i + batch.index(row) + 1}: {inner_e}")
                    print(f"         ⚠️ Error en registro {i + batch.index(row) + 1}: {inner_e}")
                    continue

    # 7. Verificar conteo final
    pg_cursor.execute("SELECT COUNT(*) FROM precios")
    count_pg = pg_cursor.fetchone()[0]

    pg_conn.close()

    # 8. Mostrar resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("=" * 70)
    print(f"   Registros en SQLite:      {count_sqlite}")
    print(f"   Registros insertados:     {total_insertados}")
    print(f"   Registros con error:      {errores}")
    print(f"   Registros en PostgreSQL:  {count_pg}")
    print("-" * 70)

    if errores_detalle:
        print("\n🔍 Detalle de errores (primeros 10):")
        for detalle in errores_detalle[:10]:
            print(f"   - {detalle}")

    if count_sqlite == count_pg and errores == 0:
        print("\n✅ ¡MIGRACIÓN EXITOSA! Todos los registros se migraron correctamente.")
    elif count_sqlite == count_pg and errores > 0:
        print("\n⚠️  Migración completada con errores, pero el conteo final coincide.")
        print("   Revisa los errores detallados para saber qué registros fallaron.")
    else:
        print(f"\n❌ ERROR: El conteo no coincide. Faltan {count_sqlite - count_pg - errores} registros (sin contar errores).")
        print("   Revisa los errores y vuelve a ejecutar el script.")

    print("=" * 70)

if __name__ == "__main__":
    migrar()