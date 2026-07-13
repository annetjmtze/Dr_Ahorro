# 🤖 Dr. Ahorro Bot

> Bot conversacional multicanal para consultar información y precios públicos de medicamentos en México utilizando **Claude (Anthropic)** como motor de inteligencia artificial y **Web Scraping** para obtener precios reales desde farmacias con sitios web.

---

# 📌 Tabla de Contenidos

- [🚀 Características](#-características)
- [🛠️ Tecnologías](#️-tecnologías)
- [🧠 Arquitectura](#-arquitectura)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [📋 Requisitos Previos](#-requisitos-previos)
- [⚙️ Instalación y Configuración](#️-instalación-y-configuración)
- [🚀 Uso](#-uso)
- [🌐 Web Scraping de Farmacias](#-web-scraping-de-farmacias)
- [💾 Base de Datos de Historial de Precios](#-base-de-datos-de-historial-de-precios)
- [ Variables de Entorno](#-variables-de-entorno)
- [🧪 Posibles Errores y Soluciones](#-posibles-errores-y-soluciones)
- [🚧 Mejoras Futuras](#-mejoras-futuras)
- [🙏 Créditos](#-créditos)
- [📜 Licencia](#-licencia)

---

# 🚀 Características

- ✅ Funciona tanto en **Telegram** como en **WhatsApp**.
- ✅ Utiliza **Claude (Anthropic)** para interpretar consultas sobre medicamentos.
- ✅ Obtiene precios públicos mediante **Web Scraping** desde farmacias con sitios web.
- ✅ Guarda los resultados del scraping en formato **JSON**.
- ✅ Almacena el historial de precios en una base de datos SQLite.
- ✅ Consulta automáticamente los precios registrados durante las últimas 24 horas.
- ✅ Normaliza nombres comerciales (ej. Tempra, Aspirina, Ozempic) utilizando Claude antes de consultar la base de datos.
- ✅ Muestra un ranking de farmacias ordenado por precio.
- ✅ Si no existen precios disponibles, responde con la ficha del medicamento y continúa buscando información.
- ✅ Probado con usuarios reales mediante WhatsApp utilizando Twilio Sandbox.
- ✅ Arquitectura modular y fácil de mantener.
- ✅ Respuestas adaptadas al formato de cada plataforma.
- ✅ Fácil de extender a nuevos canales como Discord o Messenger.
- ✅ Registro automático del webhook de WhatsApp.
- ✅ Detecta automáticamente si una farmacia publica precios en HTML estático o requiere contenido dinámico.
- ✅ Implementa una estrategia híbrida de obtención de precios:
- Web Scraping para sitios con precios públicos.
- OCR para extraer precios desde imágenes cuando el HTML no los contiene.
- ✅ Documenta automáticamente los hallazgos técnicos de cada farmacia evaluada.

---

# 🛠️ Tecnologías

| Tecnología | Uso |
|------------|-----|
| Python 3.10+ | Lenguaje principal |
| Flask | Webhook para WhatsApp |
| Twilio API | Integración con WhatsApp |
| python-telegram-bot | Bot de Telegram |
| Anthropic Claude | Procesamiento mediante IA |
| Requests | Solicitudes HTTP |
| BeautifulSoup4 | Extracción de información HTML |
| lxml | Parser HTML |
| python-dotenv | Variables de entorno |
| SQLite | Base de datos para historial de precios |
| ngrok | Exposición del servidor local |

---

# 🧠 Arquitectura

```text
                     Telegram
                         │
                         ▼
              ┌────────────────────┐
              │ Telegram Handler   │
              └─────────┬──────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │ Claude (Anthropic LLM) │
            │ Normalizador           │
            └─────────┬──────────────┘
                      │
                      │◄────────────────────────────────────────┐
          ┌───────────┴──────────────┐                          │
          │                          │                          │
          ▼                          ▼                          │
   Web Scraping                 OCR                             │
(Requests + BS4)        (Tesseract + Claude)                    │
          │                          │                          │
          └───────────┬──────────────┘                          │
                      ▼                                         │
            ┌──────────────────┐                                │
            │   Base de Datos  │◄────────────────────────────────┘
            │    (SQLite)      │
            └──────────────────┘
                      │
                      ▼
            WhatsApp / Telegram
```
---

## Flujo de consulta

```text
Usuario
   │
   ▼
WhatsApp / Telegram
   │
   ▼
Claude normaliza el medicamento
(Ej. "Tempra" → "Paracetamol 500 mg")
   │
   ▼
Consulta SQLite
(precios últimas 24 horas)
   │
   ├───────────────┐
   │               │
Hay precios      No hay precios
   │               │
   ▼               ▼
Ranking          Ficha del medicamento
de farmacias     + "Buscando precios..."
```
---

# 💬 Flujo de respuesta del bot

Cuando un usuario envía el nombre de un medicamento, el sistema sigue el siguiente proceso:

1. Claude normaliza el nombre del medicamento.
2. Se consulta la base de datos SQLite.
3. Si existen precios registrados durante las últimas 24 horas:
   - Se ordenan de menor a mayor.
   - Se muestran promociones disponibles.
   - Se indica cuándo fueron actualizados.
4. Si no existen registros:
   - Claude genera una ficha del medicamento.
   - El bot informa que continúa buscando precios.

Este flujo permite responder incluso cuando todavía no existe información de precios para un medicamento.

---

### Principio de diseño

El sistema está dividido en módulos independientes.

- Los **handlers** reciben los mensajes desde Telegram y WhatsApp.
- El **normalizador** procesa la consulta mediante Claude.
- El **módulo de Web Scraping** consulta precios públicos cuando es necesario.
- Los resultados del scraping se almacenan en archivos JSON para su reutilización y análisis.

---

# 📁 Estructura del Proyecto

```text
dr-ahorro-bot/
│
├── bot/
│   ├── __init__.py
│   ├── telegram_handler.py
│   └── whatsapp_handler.py
│
├── config/
│   └── __init__.py
│
├── data/
│   ├── __init__.py
│   └── scrapers/
│       ├── web_scraper.py
│       └── resultados_farmacias.json
│
├── llm/
│   ├── __init__.py
│   └── normalizer.py
│
├── screenshots/
│
├── hallazgos_scraping.md
├── .env
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

---

# 📋 Requisitos Previos

Antes de ejecutar el proyecto necesitas:

- Python 3.14 o superior
- Cuenta de Anthropic
- Cuenta de Twilio
- Bot creado mediante BotFather
- ngrok instalado

---

# ⚙️ Instalación y Configuración

## 1. Clonar el repositorio

```bash
git clone https://github.com/tu_usuario/dr-ahorro-bot.git

cd dr-ahorro-bot
```

---

## 2. Crear un entorno virtual

### Windows

```cmd
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 4. Configurar variables de entorno

Copiar el archivo:

```bash
cp .env.example .env
```

Completar las credenciales:

```env
# Telegram
TELEGRAM_BOT_TOKEN=

# Claude
ANTHROPIC_API_KEY=

# Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=

# Webhook
WEBHOOK_URL=https://xxxxx.ngrok-free.app/webhook

PORT=5000
```

---

## 5. Ejecutar ngrok

```bash
ngrok http 5000
```

Actualizar la URL pública en:

```env
WEBHOOK_URL=https://tu-url.ngrok-free.app/webhook
```

---

# 🚀 Uso

## Ejecutar únicamente Telegram

```bash
python main.py --channel telegram
```

---

## Ejecutar únicamente WhatsApp

```bash
python main.py --channel whatsapp --port 5000
```

---

## Ejecutar ambos canales

```bash
python main.py --channel all
```

---

# 🌐 Web Scraping de Farmacias

El proyecto incorpora un módulo de Web Scraping encargado de consultar precios públicos de medicamentos disponibles en farmacias mexicanas.

## Objetivo

Obtener precios reales para complementar la información proporcionada por el bot utilizando únicamente información pública.

---

## Estrategia de obtención de precios

El proyecto sigue una estrategia híbrida.

### 1. Web Scraping

Se consulta el HTML público del sitio web mediante:

- Requests
- BeautifulSoup4
- Selectores CSS
- Parser lxml

Cuando el precio aparece directamente en el código fuente (Ctrl+U), puede extraerse mediante scraping tradicional.

---

### 2. OCR

Muchas farmacias muestran el precio únicamente dentro de imágenes o contenido generado dinámicamente mediante JavaScript.

En esos casos el proyecto utiliza OCR para extraer automáticamente el precio desde capturas de pantalla.

Esta estrategia permite cubrir una mayor cantidad del mercado mexicano.

---

## Diagnóstico previo

Antes de desarrollar un scraper se realiza un diagnóstico del sitio web.

1. Abrir la página del medicamento.
2. Presionar **Ctrl + U** para visualizar el código fuente.
3. Buscar el precio.

Si el precio aparece en el código fuente:

✅ Se utiliza BeautifulSoup.

Si el precio no aparece:

➡️ Se documenta el caso para utilizar OCR.

---

## Cobertura

Actualmente el proyecto considera dos grupos principales:

- Farmacias con precios públicos accesibles mediante HTML.
- Farmacias cuyos precios requieren OCR.

La combinación de ambas técnicas permite ampliar significativamente la cobertura de medicamentos.

---

## Ejecutar el scraper

```bash
python data/scrapers/web_scraper.py
```

---

## Resultado

Los datos obtenidos se almacenan automáticamente en:

```text
data/scrapers/resultados_farmacias.json
```

Ejemplo:

```json
{
  "medicamento_buscado": "Paracetamol",
  "nombre_encontrado": "Paracetamol 500 mg",
  "farmacia": "Farmacia de ejemplo",
  "precio": 49.50,
  "precio_promedio": 38.00,
  "vigencia_precio": "2026-07-15",
  "url_producto": "https://...",
  "fuente": "scrape_web",
  "fecha_consulta": "2026-07-07T10:30:00"
}
```

---
# 📄 Hallazgos Técnicos

Durante el desarrollo se documentan las pruebas realizadas sobre diferentes farmacias mexicanas.

Toda la información se registra en:

```text
hallazgos_scraping.md
```

Cada análisis incluye:

- Nombre de la farmacia.
- URL analizada.
- Disponibilidad del precio.
- Resultado de Ctrl+U.
- Si el sitio utiliza JavaScript.
- Posibilidad de realizar Web Scraping.
- Necesidad de OCR.
- Observaciones técnicas.
- Estado del scraper.
---

# 🔧 Variables de Entorno

| Variable | Descripción | Obligatoria |
|-----------|-------------|-------------|
| TELEGRAM_BOT_TOKEN | Token del bot de Telegram | ✅ |
| ANTHROPIC_API_KEY | API Key de Claude | ✅ |
| TWILIO_ACCOUNT_SID | Cuenta de Twilio | WhatsApp |
| TWILIO_AUTH_TOKEN | Token de Twilio | WhatsApp |
| TWILIO_WHATSAPP_NUMBER | Número Sandbox | WhatsApp |
| WEBHOOK_URL | URL pública de ngrok | WhatsApp |
| PORT | Puerto de Flask | No |

---

# 🧪 Posibles Errores y Soluciones

| Error | Solución |
|--------|----------|
| ModuleNotFoundError | Ejecutar `pip install -r requirements.txt` |
| Error 404 en Telegram | Verificar el Token del bot |
| Webhook no registrado | Revisar la URL pública de ngrok |
| Claude no responde | Verificar la API Key |
| WhatsApp no responde | Revisar Twilio y el webhook |
| Error durante el scraping | Verificar la estructura HTML del sitio o actualizar los selectores CSS |

---

# 🚧 Mejoras Futuras

- Consultar múltiples farmacias automáticamente.
- Integrar Selenium para sitios con contenido dinámico.
- Automatizar el flujo OCR para farmacias sin HTML público.
- Detectar automáticamente cuándo utilizar Scraping u OCR.
- Calcular precios promedio entre múltiples farmacias.
- Implementar caché para reducir consultas repetidas.
- Almacenar historial de búsquedas en una base de datos.
- Exponer una API REST para consultar medicamentos y precios.

---

# 🙏 Créditos

Proyecto desarrollado con fines educativos para practicar:

- Arquitectura de software en Python.
- Bots conversacionales.
- Integración con Telegram.
- Integración con WhatsApp mediante Twilio.
- Webhooks con Flask.
- Consumo de APIs.
- Modelos LLM con Anthropic Claude.
- Técnicas de Web Scraping con Requests y BeautifulSoup.

---

# 📜 Licencia

Este proyecto fue desarrollado con fines académicos y educativos.

---

⭐ Si este proyecto te resulta útil, considera darle una estrella al repositorio.
