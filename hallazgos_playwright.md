# Hallazgos – Agente Playwright

## Resumen de ejecución

Se ejecutó `python data/agents/playwright_agent.py "paracetamol"` con las tres farmacias definidas en `hallazgos_scraping.md`.

| Farmacia              | ¿Funcionó BeautifulSoup? | ¿Funcionó Playwright? | Observación |
|-----------------------|---------------------------|------------------------|-------------|
| Farmacias del Ahorro  | Sí (precio en HTML)       | No (no se detectó buscador ni precio en fallback) | La página parece usar protección anti-bot o carga asíncrona que el fallback directo no resuelve. Se requiere investigación adicional (esperar un elemento específico o usar stealth). |
| Farmacias Benavides   | Sí (con regex en JSON)    | **Sí** (precio extraído del DOM y por Claude) | El buscador se detectó automáticamente y el precio se obtuvo directamente del DOM. Además Claude Vision confirmó el valor. La captura se guardó en R2. |
| Probemedic            | Sí (precio en HTML)       | **Sí** (precio extraído del DOM y por Claude) | El buscador se detectó y el precio se extrajo correctamente. Funciona igual que con BS4 pero ahora con screenshot histórico. |

## ¿Resuelve Playwright los casos que fallaban con BeautifulSoup?

- **Farmacias Benavides y Probemedic** ya funcionaban con BeautifulSoup, por lo que Playwright no era estrictamente necesario para el scraping de precio. Sin embargo, **aporta un valor adicional**: la captura de pantalla almacenada en R2 como evidencia visual del precio en ese momento.
- **Farmacias del Ahorro** sí funcionaba con BeautifulSoup, pero el agente Playwright no logró extraer el precio en esta prueba. Esto demuestra que, aunque Playwright ejecuta JavaScript, ciertas páginas con protecciones anti-bot (Cloudflare, captchas silenciosos) pueden requerir configuraciones adicionales como rotación de User-Agents, proxies residenciales o navegación stealth.

## Ventajas del agente Playwright sobre el scraper tradicional

- **Evidencia visual**: cada ejecución guarda una captura de pantalla en R2, generando un histórico gráfico de los precios.
- **Extracción híbrida**: combina selectores CSS, Claude Vision y regex sobre HTML crudo, lo que lo hace más robusto ante cambios de layout.
- **Detección automática del buscador**: no requiere conocer el selector exacto; utiliza JavaScript para encontrar el campo de búsqueda más probable.
- **Manejo de errores**: si una farmacia falla, el proceso continúa con las demás sin interrumpirse.

## Limitaciones encontradas

- **Farmacias del Ahorro**: el fallback a la URL de producto no mostró el precio en el DOM ni en el HTML crudo. Posibles causas:
  - Protección Cloudflare que devuelve un challenge en lugar del contenido real.
  - El precio se carga mediante una API AJAX que no se ejecuta con `networkidle`.
  - Necesidad de simular scroll o interacción para activar la carga del módulo de precio.

## Próximos pasos sugeridos

- Implementar técnicas anti-detección (Playwright Stealth, rotación de proxies).
- Para Farmacias del Ahorro, probar con una búsqueda real (si se logra bypassear el buscador) o usar su API interna si se descubre.
- Ampliar el agente para más farmacias aprovechando la detección automática del buscador.

## Registros en BD obtenidos en esta prueba

Se generaron múltiples registros con `fuente='agente_playwright'` para Benavides (precio $918.00) y Probemedic ($23.00). Las imágenes correspondientes se almacenaron localmente y en R2 (cuando estuvo habilitado).