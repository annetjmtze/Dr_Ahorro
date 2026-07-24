## Checklist técnico (previo a pruebas)

- [x] `SELECT COUNT(*) FROM precios WHERE url NOT LIKE 'https://%'` → **0** (todas las URLs son válidas)
- [x] Búsqueda "ibuprofeno" → **0 resultados de Buscapina** (filtro por farmacia funciona)
- [x] Búsqueda "paracetamol" → **0 duplicados de misma farmacia en las respuestas del bot** (deduplicación activa, script limpió duplicados del mismo día)
- [x] Links de Rappi/Uber Eats → **abren en la app móvil** (deep link generado correctamente)
- [x] Logs de Railway → **sin errores de contar_por_fuente** (bot arranca sin problemas)