# Hallazgos de scraping - Día 2

## Resumen ejecutivo
- **Fecha**: 2026-07-07
- **Objetivo**: Obtener al menos un precio real de paracetamol en JSON.
- **Resultado**: 6 registros JSON de 3 farmacias (Farmacias del Ahorro, Benavides, Probemedic).

## Análisis por farmacia

### Farmacias del Ahorro
- **URL**: https://www.fahorro.com/paracetamol-500-mg-oral-20-tabletas-marca-del-ahorro.html
- **¿Precio en HTML estático?**: Sí
- **Método**: requests + BeautifulSoup
- **Selector**: `[data-price-type="oldPrice"] .price`
- **Precio**: $31.00

### Farmacias Benavides
- **URL**: https://www.benavides.com.mx/perfalgan-paracetamol-1-ud-frasco-ampula
- **¿Precio en HTML estático?**: Sí (también en script GA4)
- **Método**: requests + BeautifulSoup + extracción desde script
- **Precio**: $918.00

### Probemedic
- **URLs**: 4 productos diferentes
- **¿Precio en HTML estático?**: Sí
- **Método**: requests + BeautifulSoup + regex
- **Precios**: $23.00, $48.00, $25.92, $43.00

### Farmacias Guadalajara (descartada)
- **Problema**: Timeout en todas las peticiones (posible bloqueo anti-bot)
- **Tiempo invertido**: >30 min
- **Decisión**: Se aplicó la regla de los 30 minutos y se descartó.

## Conclusión
Se obtuvieron 6 precios reales de 3 farmacias diferentes, cumpliendo el objetivo.