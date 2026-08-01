# Feedback y Hallazgos - Semana 5
**Fecha de pruebas:** 31 de Julio de 2026  
**Proyecto:** Dr. Ahorro (Agente de mapas con Playwright y motor de costo-beneficio)

---

## 1. Resumen de Pruebas en Producción

Durante el primer viernes de pruebas en vivo con usuarios reales, se evaluó la integración del onboarding de zona, el agente automatizado de mapas mediante Playwright (sin costo de API de Google Maps) y el motor de recomendación en lenguaje natural.

### Criterios de Aceptación Evaluados:
* **Onboarding de zona:** Probado con usuarios reales ingresando códigos postales (ej. `60190` en Uruapan) y ubicaciones compartidas por pin de WhatsApp. El flujo detectó correctamente la falta de zona registrada y solicitó las coordenadas de forma interactiva.
* **Mapa visual vía WhatsApp:** Playwright generó exitosamente los screenshots con pines de ubicación y farmacias cercanas (ej. zona Uruapan y Cholula, Puebla), enviándolos de manera directa al chat.
* **Recomendación y Precios:** El bot cruzó la ubicación con la base de datos de precios reales, arrojando alternativas económicas (ej. sugerencias en Farmacias Similares) y alertas de receta médica cuando el medicamento lo requería (ej. Mounjaro, Clonazepam).

---

## 2. Preguntas Específicas de Validación con Usuarios

### ¿El mapa fue útil o confuso?
* **Hallazgo:** El mapa generado por Playwright es visualmente claro y ubica de forma correcta las sucursales principales (Farmacias Similares, Del Ahorro, Guadalajara). 
* **Punto de mejora detectado:** En algunas pruebas iniciales con coordenadas genéricas o búsquedas amplias (como la vista por defecto de EE. UU. o regiones lejanas antes de afinar el pin), el mapa tardó en centrarse o mostró un radio muy abierto. Sin embargo, al usar la ubicación precisa por GPS o código postal (ej. `60190`), el enfoque mejoró notablemente para el usuario final.

### ¿La recomendación final les ayudó a decidir?
* **Sí.** Los usuarios destacaron que ver el comparativo directo de precios (por ejemplo, opciones desde $9.00 o $24.00 MXN) junto con la sugerencia explícita de la alternativa más barata ahorra tiempo de búsqueda y llamadas a sucursales. 
* Adicionalmente, el filtro de seguridad ("Este medicamento requiere receta médica") aportó contexto crítico antes de la compra para fármacos controlados.

### ¿El onboarding de zona fue claro?
* **Sí, apto para usuarios 60+.** El mensaje del bot (`"Para mostrarte las farmacias más cercanas, ¿en qué zona buscas? Escribe tu colonia y ciudad... o toca el clip y comparte tu ubicación"`) demostró ser sumamente intuitivo. 
* Los usuarios lograron completar el registro tanto escribiendo su zona de manera natural (ej. *“Cholula, Puebla”*) como utilizando la función nativa de compartir ubicación por WhatsApp sin requerir instrucciones previas.

---

## 3. Registro de Incidencias y Ajustes Técnicos

1. **Casos sin stock local:** Cuando una zona específica no cuenta con el medicamento en la base de datos local (ej. *Mounjaro* o búsquedas en ciertas áreas de Uruapan), el bot reacciona correctamente sugiriendo la alternativa nacional más barata o indicando la necesidad de intentar más tarde, evitando respuestas vacías.
2. **Comando `/zona`:** Funciona de manera óptima para permitir a los usuarios reconfigurar su ubicación en cualquier momento del flujo conversacional.