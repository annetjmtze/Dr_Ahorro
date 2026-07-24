import sqlite3
import os

DB_PATH = "data/precios.db"

def verificar_registros():
    if not os.path.exists(DB_PATH):
        print(f"❌ La base de datos '{DB_PATH}' no existe. Asegúrate de que los agentes se hayan ejecutado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ver qué tablas existen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📋 Tablas en {DB_PATH}:", [t[0] for t in tables])
    
    # Si existe la tabla 'precios' (o la que uses)
    if ('precios',) in tables:
        cursor.execute("""
            SELECT medicamento, farmacia, precio, url, fuente, fecha 
            FROM precios 
            ORDER BY fecha DESC 
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if rows:
            print("\n📊 Últimos 10 registros guardados:")
            print("-" * 80)
            for row in rows:
                link = row[3][:50] + "..." if row[3] and len(row[3]) > 50 else row[3]
                print(f"💊 {row[0]} | 🏪 {row[1]} | 💰 ${row[2]} | 🔗 {link} | 📱 {row[4]} | 📅 {row[5]}")
        else:
            print("⚠️ La tabla 'precios' está vacía.")
    else:
        print("⚠️ No se encontró la tabla 'precios'. Revisa la estructura de la base de datos.")
    
    conn.close()

if __name__ == "__main__":
    verificar_registros()
    