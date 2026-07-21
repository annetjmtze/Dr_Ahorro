import unittest

class TestDatabaseImports(unittest.TestCase):
    def test_all_public_functions_exist(self):
        # Importar todas las funciones públicas de data.database
        from data.database import (
            get_precios,
            save_precio,
            contar_por_fuente,
            get_resumen,
            get_last_precios,
            count_precios,
            init_db,
            validar_coherencia_producto,
            validar_precio
        )
        # Si llega aquí, todas existen
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()