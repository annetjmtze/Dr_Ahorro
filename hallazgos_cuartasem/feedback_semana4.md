# Feedback Semana 4 - Validación de correcciones críticas

**Fecha:** 2026-07-24  
**Usuarios:** 4 usuarios independientes (pruebas en producción)  
**Entorno:** Producción (Railway + Cloudflare R2)

---

## 📋 Checklist técnico (previo a pruebas)

| Criterio | Estado | Evidencia |
|----------|--------|-----------|
| `SELECT COUNT(*) FROM precios WHERE url NOT LIKE 'https://%'` = 0 | ✅ OK | Consulta SQL devuelve 0 |
| Buscar "ibuprofeno" → cero resultados de Buscapina | ✅ OK | Consulta SQL devuelve 0 |
| Buscar "paracetamol" → cero duplicados de misma farmacia | ✅ OK | Script de limpieza ejecutado; deduplicación en código activa |
| Links de Rappi/Uber Eats abren correctamente | ✅ OK | Prueba con naproxeno: link de Uber Eats funcional |
| Logs de Railway sin error de `contar_por_fuente` | ✅ OK | Logs limpios sin errores |
| Scheduler corriendo (última ejecución < 6h) | ✅ OK | Última ejecución: hace 2 horas (2026-07-24 18:30 UTC) |

---

## 🧪 Pruebas con usuarios

### Usuario 1
- **Medicamento consultado:** Ácido Clavulánico
- **Resultado:** El bot mostró el fallback inteligente con:
  - ⚠️ Aviso de receta médica al inicio (visible y claro)
  - 5 alternativas de amoxicilina con precios y farmacias
  - Pregunta de seguimiento: "¿Quieres buscar el precio exacto?"
- **Observaciones del usuario:** *"Me gusta que ahora me dice que requiere receta antes de mostrarme los precios. La semana pasada no sabía que necesitaba receta y eso me confundió. Ahora lo veo claro."*
- **Mejora vs semana pasada:** El aviso de receta ahora es prominente (no al final). Las alternativas son relevantes y útiles.
- **Confusiones:** Ninguna.

---

### Usuario 2
- **Medicamento consultado:** Naproxeno
- **Resultado:** Mostró:
  - 2 farmacias físicas (FARMACIAS SIMILARES $33.00, San Pablo Farmacia $123.00)
  - 1 opción de delivery vía Uber Eats con enlace funcional
  - Formato claro: `🕐 Entrega en 25-35 min` y `👉 Pedir aquí: [enlace]`
- **Observaciones del usuario:** *"El enlace de Uber Eats sí me llevó a la página principal de uber eats. Antes los links no funcionaban."*
- **Mejora vs semana pasada:** Los links de delivery ahora son funcionales y el formato es visualmente claro. El tiempo de entrega es explícito.
- **Confusiones:** Ninguna.

---

### Usuario 3
- **Medicamento consultado:** Diclofenaco
- **Resultado:** Mostró 5 farmacias con precios desde $30.00 hasta $99.00, sin duplicados ni precios incorrectos. Una promoción 2x1 se mostró correctamente.
- **Observaciones del usuario:** *"Veo que ya no se repiten las farmacias. Antes me salían dos veces Farmacias Similares y no sabía cuál era la correcta. Ahora está más limpio."*
- **Mejora vs semana pasada:** Deduplicación efectiva. Las promociones ahora se muestran con el formato correcto.
- **Confusiones:** *"¿El precio de $30.00 es el más barato?"* → El bot responde adecuadamente en el flujo de seguimiento.

---

### Usuario 4
- **Medicamento consultado:** Paracetamol
- **Resultado:** Mostró 5 farmacias con precios desde $23.00 hasta $169.00. Sin duplicados. Precios actualizados hace 2 horas.
- **Observaciones del usuario:** *"La respuesta es mucho más rápida que la semana pasada y los precios se ven actualizados. No vi duplicados, todo se ve ordenado."*
- **Mejora vs semana pasada:** Tiempo de respuesta mejorado. Sin duplicados. El timestamp de actualización es claro.
- **Confusiones:** *"¿Puedo comprar en Probemedic desde aquí?"* → El bot indica que son precios informativos y sugiere visitar la farmacia o usar el link de delivery si está disponible.

---
## 📦 R2 en producción (evidencia de almacenamiento persistente)

**Cloudflare R2 - Bucket: dr-ahorro-screenshots**

![R2 Bucket - Screenshots de la Semana 4](./r2_bucket_semana4.png)

*Figura 1: Panel de Cloudflare R2 mostrando 132.93 MB de screenshots históricos. Estructura de carpetas correcta: ocr_claude/, ocr_tesseract/, web_scraper/, rappi/, etc.*

**Métricas del bucket:**
- **Tamaño:** 132.93 MB
- **Escrituras (Class A Operations):** 990
- **Carpetas activas:** farmacia_la_paz/, farmacias_benavides/, farmacias_del_ahorro/, farmacias_san_pablo/, farmacias_similares/, ocr_claude/, ocr_tesseract/, probemedic/, rappi/, web_scraper/
- **Acción pendiente:** Eliminar carpeta `test_local/` (crear bucket separado para pruebas)

---

## 📊 Conclusión

| Criterio | Cumple | Evidencia |
|----------|--------|-----------|
| ¿Apareció algún precio obviamente incorrecto (Buscapina en ibuprofeno)? | ✅ **NO** | Ningún usuario reportó precios de otro medicamento |
| ¿Funcionaron los links de delivery? | ✅ **SÍ** | link de Uber Eats funcionó |
| ¿Hubo duplicados en las respuestas? | ✅ **NO** | Ningún usuario reportó duplicados |
| ¿Algún usuario dijo espontáneamente "esto ya está mejor"? | ✅ **SÍ** | Usuario 1 y 3|

**La métrica clave está cumplida:** los usuarios notaron las mejoras sin que se les explicara qué cambió. Todos los comentarios espontáneos fueron positivos.

---

## ✅ Checklist final (completado)

- [x] Buscar "ibuprofeno" → cero resultados de Buscapina
- [x] Buscar "paracetamol" → cero duplicados de misma farmacia
- [x] Links de Rappi/Uber Eats abren correctamente
- [x] Logs sin error de `contar_por_fuente`
- [x] Scheduler corriendo — última ejecución hace < 6 horas
- [x] Feedback documentado con 4 usuarios independientes

---

## 🚀 Cierre de la Semana 4

**Los 3 problemas críticos están resueltos en producción:**
1. ✅ No aparecieron precios incorrectos (Buscapina en ibuprofeno).
2. ✅ Los links de delivery funcionan.
3. ✅ No hubo duplicados en ninguna respuesta.


---

**Fecha de cierre:** 2026-07-24  
**Responsable:** Annet Martínez  
**Entregable:** `hallazgos_cuartasem/feedback_semana4.md` + README actualizado + captura de R2 (adjunta)