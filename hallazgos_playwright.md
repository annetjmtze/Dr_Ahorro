# Hallazgos – Agente Playwright

## Resumen de ejecución

Se ejecutó el agente Playwright con 5 medicamentos (paracetamol, ibuprofeno, diclofenaco, fluoxetina, metformina) en 7 farmacias.

## Resultados por farmacia

| Farmacia | ¿Detecta buscador? | ¿Extrae precio? | Observaciones |
|----------|-------------------|-----------------|---------------|
| Farmacias del Ahorro | No | No | La página bloquea el acceso (posible protección anti‑bot). Se omite sin detener el proceso. |
| Farmacias Benavides | Sí | Parcial (2/5) | Extrajo precio en 2 de 5 intentos; los fallos fueron por timeouts. |
| Probemedic | Sí | Sí (5/5) | Precio extraído del DOM en todos los medicamentos. |
| Farmacias Guadalajara | No | No | Error de protocolo HTTP/2; la página no carga en Playwright. |
| Farmacias Similares | Sí | Sí (5/5) | Buscador detectado automáticamente; precio extraído por Claude o DOM. |
| Farmacias San Pablo | No | No | No se detectó buscador; la URL de respaldo no mostró precio. |
| Farmacia La Paz | Sí | Sí (4/5) | Buscador detectado; precios extraídos con regex o Claude. Solo un timeout en un caso. |

## Registros obtenidos

Se generaron **16 registros** en la base de datos con `fuente='agente_playwright'` y precio válido.  
Cada registro tiene una captura de pantalla asociada, almacenada localmente o en Cloudflare R2 según la configuración.

## Capturas en Cloudflare R2

Las imágenes se guardan con la ruta `{farmacia}/{medicamento}/{timestamp}.png`.  
Cuando `USE_R2=true`, las URLs públicas quedan como:  
`https://<cuenta>.r2.cloudflarestorage.com/dr-ahorro-screenshots/benavides/paracetamol/20260714_211839.png`

## Comparativa con BeautifulSoup

- **Probemedic y Benavides** ya funcionaban con BeautifulSoup, por lo que Playwright no era indispensable, pero aporta el respaldo visual (screenshot).
- **Farmacias Similares y La Paz** antes solo se consultaban por OCR; ahora Playwright las integra directamente en el flujo automatizado, extrayendo precios de manera confiable.
- **Farmacias del Ahorro, Guadalajara y San Pablo** no pudieron ser scrapeadas con Playwright debido a protecciones anti‑bot o errores de protocolo. Se mantienen como candidatas para OCR.

## Conclusión

Playwright ha demostrado ser una herramienta eficaz para farmacias con carga dinámica de JavaScript (Similares, La Paz) y para robustecer el monitoreo de precios con capturas históricas. Sin embargo, no es una solución universal contra bloqueos avanzados. El agente cumple con todos los criterios de aceptación, generando más de los 5 registros requeridos.