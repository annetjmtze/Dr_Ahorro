# 📝 feedback_usuarios.md

## Fecha
10 de julio de 2026

## Objetivo

Validar el funcionamiento del bot de WhatsApp con usuarios reales, observando cómo interactúan sin explicarles el funcionamiento interno del sistema.

---

# Usuario 1

### Medicamento consultado
Paracetamol

### Respuesta del bot

El bot reconoció correctamente el medicamento y consultó la base de datos de precios.

Mostró un ranking de farmacias con precios y promociones disponibles.

### Resultado

✅ Éxito.

### Observaciones

- El usuario obtuvo precios reales.
- El formato fue fácil de leer desde WhatsApp.
- Se mostró la fecha de actualización de los precios.
- Se detectó un problema: algunos registros aparecieron duplicados (Probemedic, Farmacias del Ahorro y Benavides).
- También se detectó un precio incorrecto para Benavides ($918.00), probablemente debido a un error en el proceso de scraping u OCR.

### Medicamento consultado
Ozempic

### Respuesta del bot

El bot identificó correctamente el nombre comercial "Ozempic" y lo normalizó como **Semaglutida**.

Como no existían registros recientes en la base de datos, respondió con la ficha del medicamento e indicó que continúa buscando precios.

### Resultado

✅ Comportamiento esperado.

### Observaciones

- El usuario recibió información útil aun sin existir precios.
- El mensaje evita dejar al usuario sin respuesta.
- Será necesario ampliar la base de datos para incluir más medicamentos.

---

# Usuario 2 (61 años)

### Medicamento consultado
Aspirina

### Respuesta del bot

El bot mostró correctamente la ficha del medicamento:

- Nombre genérico.
- Uso principal.
- Requiere receta.

Después informó que aún no existen precios disponibles.

### Resultado

✅ Correcto.

### Observaciones

- La información médica fue clara.
- El usuario siempre obtiene una respuesta, incluso cuando no hay precios registrados.

---

# Usuario 3 (65 años)

### Medicamento consultado
Saridon

### Respuesta del bot

El bot identificó correctamente el medicamento y mostró:

- Nombre genérico.
- Uso principal.
- Si requiere receta.

Posteriormente indicó que los precios aún están siendo buscados.

### Resultado

✅ Correcto.

### Observaciones

- El modelo reconoció un medicamento comercial menos común.
- La normalización de nombres funcionó correctamente.

---

# Usuario 4 (25 años)

### Medicamento consultado
Mounjaro

### Respuesta del bot

El usuario consultó el medicamento **Mounjaro**.

El bot identificó correctamente el nombre comercial y lo normalizó como **tirzepatida**.

Mostró la siguiente información:

- Nombre genérico: Tirzepatida.
- Uso principal: Tratamiento de diabetes mellitus tipo 2.
- Requiere receta: Sí.

Como no existían registros recientes en la base de datos, el bot respondió con el mensaje:

> 🔍 Buscando precios... Pronto tendremos información de farmacias cercanas.

### Resultado

✅ Funcionamiento correcto.

### Observaciones

- El bot reconoció correctamente un medicamento de marca sin necesidad de que el usuario escribiera el nombre genérico.
- La respuesta fue clara y fácil de entender.
- El usuario siempre recibió información útil, incluso cuando no había precios disponibles.
- Este caso confirma que la integración entre el LLM y el bot permite normalizar correctamente medicamentos comerciales.

--- 

# Problemas encontrados

- Existen registros duplicados en algunos resultados de precios.
- Algunos precios obtenidos mediante scraping requieren validación antes de mostrarse al usuario.
- La cobertura de medicamentos todavía es limitada debido a que la base de datos aún está en crecimiento.

---

# Aspectos que funcionaron bien

- El bot reconoce tanto nombres comerciales como nombres genéricos.
- La integración entre el LLM y la base de datos funciona correctamente.
- Cuando existen precios, estos se muestran ordenados por costo.
- Cuando no existen precios, el usuario recibe una ficha informativa útil en lugar de un mensaje de error.
- El formato de WhatsApp es sencillo y fácil de entender.

---

# Mejoras para la siguiente versión

- Eliminar registros duplicados en la consulta de precios.
- Validar precios extremos antes de mostrarlos al usuario.
- Agregar más medicamentos y farmacias a la base de datos.
- Mostrar la presentación del medicamento (tabletas, cápsulas, suspensión, etc.).
- Incorporar ubicación del usuario para mostrar farmacias cercanas.

---

# Conclusiones

La prueba con usuarios reales permitió comprobar que el flujo principal del bot funciona correctamente. Los usuarios pudieron consultar medicamentos utilizando nombres comerciales y genéricos, y siempre recibieron una respuesta útil.

Las pruebas también ayudaron a identificar áreas de mejora, principalmente relacionadas con la calidad de los datos obtenidos mediante scraping (precios incorrectos o duplicados) y la necesidad de ampliar la cobertura de medicamentos. En general, el objetivo del MVP se cumplió, ya que usuarios no técnicos pudieron interactuar con el bot de WhatsApp y obtener información relevante sobre medicamentos sin necesidad de asistencia.