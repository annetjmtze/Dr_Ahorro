import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.database import get_connection, IS_PROD

def limpiar_urls():
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE precios SET url = NULL WHERE url NOT LIKE 'https://%' OR url LIKE '%add-product-icon%'"
    cursor.execute(sql)
    conn.commit()
    print(f"✅ URLs limpiadas. Filas afectadas: {cursor.rowcount}")
    conn.close()

if __name__ == "__main__":
    limpiar_urls()
    