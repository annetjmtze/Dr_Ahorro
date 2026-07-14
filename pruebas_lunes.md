# 📋 Pruebas del Lunes – 13 de julio de 2026

## 🌐 Configuración de la prueba

| Aspecto | Detalle |
|----------|---------|
| Bot desplegado en | Railway |
| Webhook configurado | Twilio WhatsApp Business API |
| Base de datos | SQLite con datos de prueba (582 registros OCR Claude, 706 registros OCR Tesseract y 68 registros por Web Scraping) |
| Modelo LLM | `claude-haiku-4-5` (verificado con test) |
| Fecha de prueba | 13 de julio de 2026 |

---

# 📱 Cuenta 1 – Annet Martínez (Cuenta de desarrollo)

| Mensaje enviado | Respuesta del bot | Tiempo | Estado |
|-----------------|-------------------|---------|--------|
| paracetamol | ✅ Mostró 2 precios: Farmacia del Ahorro ($45.50) y Farmacia San Pablo ($48.00) | < 2 s | ✅ |
| acetaminofén | ✅ Mostró los mismos precios que paracetamol | < 2 s | ✅ |
| ibuprofeno | ✅ Mostró 1 precio (Farmacias Similares – $89.00, promoción $79.50) | < 2 s | ✅ |
| metformina | ✅ Mostró 1 precio (Farmacia del Ahorro – $120.00) | < 2 s | ✅ |
| aspirina | ✅ Mensaje de fallback indicando que aún no hay precios registrados | < 3 s | ✅ |
| saridon | ✅ Mensaje de fallback | < 3 s | ✅ |
| diclofenaco | ✅ Mensaje de fallback | < 3 s | ✅ |
| medicamento_falso | ✅ Mensaje de fallback | < 3 s | ✅ |

---

# 📱 Cuenta 2 – Usuario externo

| Mensaje enviado | Respuesta del bot | Estado |
|-----------------|-------------------|--------|
| paracetamol | ✅ Mostró los precios correctamente | ✅ |
| acetaminofén | ✅ Mostró los precios correctamente | ✅ |
| naproxeno | ✅ Respondió con el mensaje de fallback | ✅ |
| ozempic | ✅ Respondió con el mensaje de fallback | ✅ |
| metformina | ✅ Mostró el precio registrado | ✅ |

**Observación**

El bot respondió correctamente desde una cuenta distinta a la de desarrollo, confirmando la corrección del **Bug 2**.

---

# 📱 Cuenta 3 – Usuario externo

| Mensaje enviado | Respuesta del bot | Estado |
|-----------------|-------------------|--------|
| aspirina | ✅ Respondió con mensaje de fallback | ✅ |
| saridon | ✅ Respondió con mensaje de fallback | ✅ |
| paracetamol | ✅ Mostró los precios correctamente | ✅ |

**Observación**

El usuario recibió respuestas claras y en un tiempo adecuado sin presentar errores.

---

# 🧪 Resumen de bugs verificados

| Bug | Descripción | Estado |
|------|-------------|--------|
| Bug 1 | El bot respondía con silencio cuando no existían precios en la base de datos | ✅ Resuelto |
| Bug 2 | El bot no respondía desde cuentas externas | ✅ Resuelto |
| Bug 3 | Manejo de Rate Limiting (HTTP 429) y documentación de límites | ✅ Resuelto |
| Bug 4 | Cambio del modelo a `claude-haiku-4-5` y prueba automática | ✅ Resuelto |
| Bug 5 | Normalización de nombres de medicamentos | ✅ Resuelto |
| Bug 6 | Pendiente de feedback | ⏳ Pendiente |
| Bug 7 | Pendiente de feedback | ⏳ Pendiente |

---

# 📂 Issues de GitHub

| Issue | Estado |
|-------|--------|
| Bug 1 – Silencio cuando no hay precios | ✅ Cerrado |
| Bug 2 – Sin respuesta desde cuenta externa | ✅ Cerrado |
| Bug 3 – Rate limiting | ✅ Cerrado |
| Bug 4 – Model string incorrecto | ✅ Cerrado |
| Bug 5 – Normalización de medicamentos | ✅ Cerrado |
| Bug 6 | ⏳ Pendiente |
| Bug 7 | ⏳ Pendiente |

---

# ✅ Criterios de aceptación

| Criterio | Estado |
|----------|--------|
| Medicamento no registrado responde con mensaje de fallback en menos de 5 segundos | ✅ Cumple |
| El bot responde desde una cuenta distinta a la de desarrollo | ✅ Cumple |
| El modelo `claude-haiku-4-5` está en producción y cuenta con prueba automática | ✅ Cumple |
| Los límites de Twilio y Anthropic están documentados en el README | ✅ Cumple |
| Los bugs corregidos cuentan con evidencia de funcionamiento en Railway | ✅ Cumple |

---

# 📦 Entregable

- ✅ Pull Request mergeado a `master`.
- ✅ Issues documentados y cerrados.
- ✅ Evidencia de funcionamiento en Railway.
- ✅ Pruebas realizadas desde diferentes cuentas de WhatsApp.
- ✅ Archivo `pruebas_lunes.md` incluido en el repositorio.

---

# 📎 Evidencia

Se adjuntan capturas de pantalla de las siguientes pruebas:

- Consulta de **paracetamol** mostrando precios disponibles.
- Consulta de **acetaminofén** mostrando los mismos precios tras la normalización.
- Consultas de **aspirina**, **saridon**, **diclofenaco** y medicamentos inexistentes mostrando el mensaje de fallback.
- Respuestas obtenidas desde cuentas externas verificando el funcionamiento del webhook en Railway.

---

**Fecha de cierre:** 13 de julio de 2026

**Responsable:** Annet Martínez