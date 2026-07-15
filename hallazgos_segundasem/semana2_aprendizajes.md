### Mis aprendizajes de la segunda semana.

Durante esta segunda semana logré exitosamente el flujo completo del proyecto dr. ahorro. Pues el proyecto evolucionó de un bot conversacional capaz de resp0onder preguntas sobre medicamentos, a un MVP funcional, que integra inteligencia artificial, web scraping, OCR, una base de datos histórica de precios, y dos canales de comunicación.

A lo largo de la semana se comorendieron los retos reales de construir un distema que trabaja con información pública, fuentes de datos y los usuarios finales.

----
El el día 0, se configuraron las herramientas necesarias para comenzar el desarrollo; comprendí la importancia de preparar el entorno antes de escribir código. Además de que entendí que una buena configuración inicial reduce los errores en el desarrollo.

---
En el día 1, el objetivo fue diseñar la arquitectura del sistema y conectar el bot con whatsapp; me ermitió compr4ender cómo dividir un proyecto en módulos indepenedientes.
Se implementó una arquitectura donde cada componente tiene una responsabilidad específica:

Recepción de mensajes.
Procesamiento mediante IA.
Consulta de información.
Generación de respuestas.
Además de que entendí el funcionamiento de los webhooks, y cómo whatsapp se comunica con flask mediante twilio.
Y que la inteligencia artificial no se comunica directamente con el usuario, sino que se integra dentro del flujo del sistema.

---
En el día 2, el objetivo fue obtener los precios públicos desde sitios web de farmacias mexicanas. Descubrí que hacer web scraping va más allá de utilizar beatifulsoup.
Aprendí a inspeccionar páginas web, diferenciar entre contenido estático y dinpamico, utilizar request.

Se generó un documento acerca de los hallazgos técnicos de este apartado.

---
En el día 3,  se resolvió el problema de las farmacias cuyos precios aparecen únicamente e imágenes o contenido dinámico. Aprendí que el web scraping tiene limitaciones.
A veces el contenido no aparece en el html, sino en imágenes; ahí fue necesario investigar acerca de los OCR o reconocimiento óptico de carácteres. Se pueden empleaar diversas tecnologías en conjunto para dar solución a un problema.

--- 
En el día 4, se guardaron los precios obtenidos para evitar hacer el scraping conitnuamente, pude compr4ender la importancia de una base de datos como memoria del sistema.
Empleé SQLite para almacenar los datos correspondientes.
Y el bit hace consultas para responder más rápido al usuario.

Además de que la base de datos no solo almacena in fromación, sino que permite construir funcionalidades, como el historial de precios.
Historial de precios, ranking de farmacias, consultas por fechas y comparaciones.

---
En el último día se integró todo de forma conjunta, siendo el proceso
Usuario

↓

WhatsApp / Telegram

↓

Claude interpreta el medicamento

↓

Normalización del nombre

↓

Consulta SQLite

↓

¿Hay precios?

├── Sí
│      ↓
│ Ranking de farmacias
│
└── No
       ↓
Ficha del medicamento
+
Mensaje "Buscando precios..."

ya que un proyecto real depende de la comunicació entre varios módulos y no sólo el funcionamiento de cada unno de manera individual.
Habilidades técnicas desarrolladas

---
Durante esta semana fortalecí conocimientos en:

**Inteligencia Artificial
Consumo de APIs.
Ingeniería de prompts.
Normalización automática de medicamentos.
Generación estructurada de respuestas.
**Python
Arquitectura modular.
Manejo de excepciones.
Organización del código.
Separación de responsabilidades.
**Web Scraping
Requests.
BeautifulSoup.
CSS Selectors.
Análisis de HTML.
Diagnóstico mediante Ctrl + U.
**OCR
Extracción de texto desde imágenes.
Limitaciones del scraping tradicional.
Estrategias híbridas para recuperación de datos.
**Bases de datos
SQLite.
Consultas SQL.
Almacenamiento histórico.
Filtrado por fecha.
**APIs y Webhooks
Flask.
Twilio.
Telegram Bot API.
Integración entre servicios.
**DevOps
Railway.
ngrok.
Variables de entorno.
GitHub.
Control de versiones mediante ramas.

---
El aprendizaje más importante fue entender que desarrollar un producto implica mucho más que escribir código.

Fue necesario:

Diseñar una arquitectura.
Integrar múltiples tecnologías.
Obtener información desde diferentes fuentes.
Validar datos.
Probar el sistema con usuarios reales.
Mejorar continuamente a partir del feedback recibido.

También comprendí que un MVP no necesita ser perfecto; necesita resolver un problema real para un usuario.

---
Después de esta semana me interesa profundizar en:

Selenium y Playwright para sitios completamente dinámicos.
OCR más preciso para mejorar la extracción de precios.
Automatización del scraping.
Bases de datos más robustas como PostgreSQL.
Caché para mejorar tiempos de respuesta.
Despliegue en producción con Docker y servicios en la nube.
Escalabilidad para consultar cientos de medicamentos simultáneamente.