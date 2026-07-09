# Comparativa OCR: Tesseract vs Claude Vision

*Fecha: 2026-07-08 17:51*
*Imágenes procesadas: 5*

## Resumen por imagen

### farmacia_1.jpg

**Tesseract**
- Tiempo: 0.34s
- Texto extraído:
```
p
¡Los lunes tus
compras florecen!

y nosotros

sembramos
un arbolito
por ti.
```

**Claude Vision**
- Tiempo: 2.36s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": null,
  "ciudad": null,
  "vigencia": "2025-04-30",
  "medicamentos": []
}
```

---

### farmacia_2.jpg

**Tesseract**
- Tiempo: 0.55s
- Texto extraído:
```
omociones “Y
del 20 al 29

de junio
Consulta fahorro.com/tyc

IFTACTIV

Sciacisr 10

o SERUM

VITAMIN C
E

BRIGHTENING
PEELING TONER

Farmacias del
A Ahorro Jerma
Te queremos... bien. EPecalistas en tu piel
```

**Claude Vision**
- Tiempo: 3.11s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias del Ahorro / Derma",
  "ciudad": null,
  "vigencia": "2024-06-20",
  "medicamentos": [
    {
      "nombre": "LA ROCHE-POSAY HYALU B5 CREME SURACTIF",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "VICHY LIFTACTIV COLLAGEN SPECIALIST 16 SERUM EYE",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "VITAMIN C BRIGHTENING PEELING TONER",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Protector Solar SPF 50",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    }
  ]
}
```

---

### farmacia_3.jpg

**Tesseract**
- Tiempo: 0.24s
- Texto extraído:
```

```

**Claude Vision**
- Tiempo: 4.47s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Super Farmacia",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "DETERGENTES BOLD",
      "precio_normal": null,
      "precio_promo": 23.99,
      "unidad": null
    },
    {
      "nombre": "LIMPIADORES LAVARRRILLO",
      "precio_normal": null,
      "precio_promo": 11.99,
      "unidad": "1 L"
    },
    {
      "nombre": "SUAVIZANTES BONY BLUE",
      "precio_normal": null,
      "precio_promo": 17.99,
      "unidad": "850 ml"
    },
    {
      "nombre": "JABÓN LIMÓN",
      "precio_normal": null,
      "precio_promo": 25.0,
      "unidad": "450 g"
    },
    {
      "nombre": "DETERGENTES ACE Y ARIEL",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "DETERGENTE TÍAS",
      "precio_normal": null,
      "precio_promo": 35.0,
      "unidad": null
    },
    {
      "nombre": "JABONES DE LAVANDERÍA FUERZAMBA",
      "precio_normal": null,
      "precio_promo": 17.99,
      "unidad": "350 g"
    },
    {
      "nombre": "LIMPIATRASTE SALVO LIMÓN",
      "precio_normal": null,
      "precio_promo": 50.0,
      "unidad": "500 ml"
    },
    {
      "nombre": "HIGIENICOS GRASOL Y LIMPETTE",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    }
  ]
}
```

---

### farmacia_4.jpg

**Tesseract**
- Tiempo: 0.2s
- Texto extraído:
```

```

**Claude Vision**
- Tiempo: 1.34s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "MAS FARMA",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Supositorios",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    }
  ]
}
```

---

### farmacia_5.jpg

**Tesseract**
- Tiempo: 0.48s
- Texto extraído:
```
ed o
ES Tu salud AN E)
SERVICIO A DOMICILIO

Unión. 5 £,
(Farmatodo.com.mx

“ay ':800-0186-466 Farmatodo.com.mx
```

**Claude Vision**
- Tiempo: 2.58s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmatodo",
  "ciudad": null,
  "vigencia": "2025-05-31",
  "medicamentos": [
    {
      "nombre": "Nivea crema corporal Soft Milk variedad 400 ml.",
      "precio_normal": 90.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "Nivea crema corporal Express Hydration variedad 400 ml.",
      "precio_normal": 90.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "Nivea crema corporal Milk Nutritiva variedad 400 ml.",
      "precio_normal": 90.0,
      "precio_promo": null,
      "unidad": "ml"
    }
  ]
}
```

---

## Análisis comparativo

| Criterio | Tesseract | Claude Vision |
|----------|-----------|---------------|
| Costo | Gratis (local) | ~$0.003 USD/imagen |
| Texto limpio | ✅ Excelente | ✅ Excelente |
| Fotos borrosas | ❌ Falla | ✅ Bueno a excelente |
| Precios tachados | ❌ No entiende contexto | ✅ Entiende intención |
| Abreviaciones | ❌ Las devuelve crudas | ✅ Las normaliza |
| Output estructurado | ❌ Requiere parsing | ✅ JSON directo |
| Velocidad (1000+) | ✅ Muy rápido | ⚠️ Rate limits |

## Costo estimado para 1,000 imágenes

- **Tesseract:** $0 USD (costo cero, corre local)
- **Claude Vision:** ~$3.00 USD (0.003 × 1000)

## Recomendación

- Usa **Tesseract** como primera pasada (gratis, rápido).
- Usa **Claude Vision** solo cuando Tesseract falle o necesites JSON estructurado.
- Estrategia híbrida: Tesseract para el 80% de las imágenes limpias, Claude para el 20% difíciles.
