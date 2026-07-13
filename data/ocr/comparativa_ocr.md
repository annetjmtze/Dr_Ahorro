# Comparativa OCR: Tesseract vs Claude Vision

*Fecha: 2026-07-11 21:23*
*Imágenes procesadas: 27*

## Resumen por imagen

### farmaciaguada_2.png

**Tesseract**
- Tiempo: 0.27s
- Texto extraído:
```
MI VAPOSPORIS Pornada 50 gr

Vis RESPIRATORIAS ANTDARRESCOS
oras Lorna
10 Ez tas 2 mE 2 tobas «ua VapoSports
auucésicos
EDEN PAAALFE
E z
PROFENO
ED VAS RESPRATORAS ANTICONCEPTIVOS
na
s PHARMALIFE 21 tabletas.

ANTINELAMATORIOS
FAL
90 mg 28 capsulas

16 cápeulas
```

**Claude Vision**
- Tiempo: 5.5s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": null,
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "MONTELUKAST",
      "precio_normal": 36.5,
      "precio_promo": null,
      "unidad": "tab"
    },
    {
      "nombre": "LOPERAMIDA",
      "precio_normal": 12.0,
      "precio_promo": null,
      "unidad": "tab"
    },
    {
      "nombre": "IBUPROFENO PHARMALIFE",
      "precio_normal": 37.5,
      "precio_promo": null,
      "unidad": "mg"
    },
    {
      "nombre": "ANTIINFLAMATORIOS FLARCET",
      "precio_normal": null,
      "precio_promo": 45.0,
      "unidad": "mg"
    },
    {
      "nombre": "VICK VAPORSPORTS Pomada",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": "gr"
    },
    {
      "nombre": "VICK VAPORUB Inhalador",
      "precio_normal": 110.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "LEVONORGESTREL ETINILESTRADIOL PHARMALIFE",
      "precio_normal": 39.0,
      "precio_promo": null,
      "unidad": "tab"
    },
    {
      "nombre": "LINEA COLGATE GUARD Dentífricos",
      "precio_normal": null,
      "precio_promo": 35.0,
      "unidad": null
    },
    {
      "nombre": "Bromuro de Piñaverio, Dimeticona",
      "precio_normal": 149.0,
      "precio_promo": null,
      "unidad": "mg"
    },
    {
      "nombre": "Bromuro de Piñaverio, Dimeticona",
      "precio_normal": 269.0,
      "precio_promo": null,
      "unidad": "cápsulas"
    },
    {
      "nombre": "ESPASPORT Naproseno Sódico",
      "precio_normal": 95.0,
      "precio_promo": null,
      "unidad": "tab"
    }
  ]
}
```

---

### farmaciagua_1.png

**Tesseract**
- Tiempo: 0.4s
- Texto extraído:
```
Básicos a precios

¡Muy bajos!

MOUIARO
25 mg/0:5 mí dosis.
24ml pluma

ocu
onu
E - E e
tl = ono
E a doss
ED ml pluma
' <a) =
a
J
pS
4,090 E
ES por 56,99900 ME vor 569990
a GATA
- Latas e Lala

OZEMPIC 1 mg /dosi.
MEGONY 25 mg /dosis. ml. "am

lps
a
Llévate $3“ o Ll = ra
»or52,3850 V=.<
en rroorama

<= 28000
“de Lialtad Proa

come
meo a TE pa
o Liévato 0.5 mg dosis. A LiÉ Nate,
PE <3,9400 o ET
ED RA

megovy" (UIPTEO
```

**Claude Vision**
- Tiempo: 4.16s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Super Farmacia",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "MOUNUARO 5 mg/0.6 ml dosis",
      "precio_normal": 4500.0,
      "precio_promo": 4090.0,
      "unidad": "ml"
    },
    {
      "nombre": "MOUNUARO 2.5 mg/0.6 ml dosis",
      "precio_normal": 4500.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "MOUNUARO 7.5 mg/0.6 ml dosis",
      "precio_normal": 8500.0,
      "precio_promo": 7990.0,
      "unidad": "ml"
    },
    {
      "nombre": "MOUNUARO 10 mg/0.6 ml dosis",
      "precio_normal": 8500.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "WEGOVY 25 mg/0.5 ml",
      "precio_normal": 5149.0,
      "precio_promo": 5099.0,
      "unidad": "ml"
    },
    {
      "nombre": "OZEMPIC 1 mg/dosis",
      "precio_normal": 5149.0,
      "precio_promo": 4280.0,
      "unidad": "ml"
    },
    {
      "nombre": "WEGOVY 1 mg/dosis",
      "precio_normal": 5149.0,
      "precio_promo": 3940.0,
      "unidad": "ml"
    },
    {
      "nombre": "OZEMPIC 0.25 mg-0.5 mg/dosis",
      "precio_normal": 5800.0,
      "precio_promo": 5140.0,
      "unidad": "ml"
    },
    {
      "nombre": "WEGOVY 1.5 mg/dosis",
      "precio_normal": 9790.0,
      "precio_promo": 2900.0,
      "unidad": "ml"
    }
  ]
}
```

---

### farmaciagua_3.png

**Tesseract**
- Tiempo: 0.27s
- Texto extraído:
```
ANTIARTRÍTICO ANÁCIDOS
PRARMALE OMEPRAZOL PHARMALIE
VO mg 7 tabletas 20 mg. 30 capsulas

S /

Etoricoxil
mamnacies —— Etoricoxib,

PAARMALIFE
10 ml ampala

a

usoroc
Er O RscUARES
100 mg Yiablta Telmisartán — rmssin

VITAMINAS

Chola" COLA vna
Honeado ouEGAS
Sm 1000 me.

10 ampoletas 20 cord

ES
NATA

HDRATACIÓN ORAL

500

iempre ahorran
siempre contigo!
```

**Claude Vision**
- Tiempo: 4.1s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Pharmalife",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "ANTIARTRTICO ETORICOXIB PHARMALIFE",
      "precio_normal": 136.0,
      "precio_promo": null,
      "unidad": "tab"
    },
    {
      "nombre": "ANTIACIDOS OMEPRAZOL PHARMALIFE",
      "precio_normal": 41.5,
      "precio_promo": null,
      "unidad": "cápsulas"
    },
    {
      "nombre": "ANTIDIABETES INSULINA NPH PHARMALIFE",
      "precio_normal": 158.5,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "UROLOGÍA SILDENAFIL PHARMALIFE",
      "precio_normal": 33.5,
      "precio_promo": null,
      "unidad": "tableta"
    },
    {
      "nombre": "CARDIOVASCULARES TELMISARTÁN PHARMALIFE",
      "precio_normal": 292.5,
      "precio_promo": null,
      "unidad": "tabletas"
    },
    {
      "nombre": "HIDRATACIÓN ORAL SUERO HIDRALFE",
      "precio_normal": 21.9,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "HIDRATACIÓN ELECTROLIT",
      "precio_normal": 49.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "HIDRATACIÓN ELECTROLIT",
      "precio_normal": null,
      "precio_promo": 40.0,
      "unidad": "ml"
    },
    {
      "nombre": "VITAMINAS OMEGA 3 PHARMALIFE NATURAL",
      "precio_normal": 128.5,
      "precio_promo": null,
      "unidad": null
    }
  ]
}
```

---

### farmacias_simi.png

**Tesseract**
- Tiempo: 0.33s
- Texto extraído:
```
597 FARMACIAS SIMILARES a

"LO MISMO PERO MAS BARATO"

cn __—_ _ _———

CJOJOJOJOJOJOJOO AL ICHORS)

u) u) u)
an, mon ali E
. metformina
xa
E E
CEFTRIAXONA 500 METFORMINA/ METFORMINA/ METFORMINA 850
MG SOLUCION SITAGLIPTINA SITAGLIPTINA MG 30 TABLETAS
209 $36.75 $374.25

$449.25

- - $30.00 $22.50

o o o
Mettormina

METFORMINA 500 METFORMINA 500 GABAPENTINA 400 METFORMINA 850
MG 60 TABLETAS MG 60 TABLETAS MG 15 CAPSULAS MG 30 TABLETAS
$6+00 $40.50 40000 $74.25

tisroo $98.25 $60.00 $51.75
```

**Claude Vision**
- Tiempo: 3.58s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Similares",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "CEFTRIAXONA 500 MG SOLUCION",
      "precio_normal": 49.0,
      "precio_promo": 36.75,
      "unidad": null
    },
    {
      "nombre": "METFORMINA / SITAGLIPTINA",
      "precio_normal": 499.0,
      "precio_promo": 374.25,
      "unidad": null
    },
    {
      "nombre": "METFORMINA / SITAGLIPTINA",
      "precio_normal": 599.0,
      "precio_promo": 449.25,
      "unidad": null
    },
    {
      "nombre": "METFORMINA 850 MG 30 TABLETAS",
      "precio_normal": 30.0,
      "precio_promo": 22.5,
      "unidad": null
    },
    {
      "nombre": "METFORMINA 500 MG 60 TABLETAS",
      "precio_normal": 54.0,
      "precio_promo": 40.5,
      "unidad": null
    },
    {
      "nombre": "METFORMINA 500 MG 60 TABLETAS",
      "precio_normal": 99.0,
      "precio_promo": 74.25,
      "unidad": null
    },
    {
      "nombre": "GABAPENTINA 400 MG 15 CAPSULAS",
      "precio_normal": 131.0,
      "precio_promo": 98.25,
      "unidad": null
    },
    {
      "nombre": "METFORMINA 850 MG 30 TABLETAS",
      "precio_normal": 69.0,
      "precio_promo": 51.75,
      "unidad": null
    }
  ]
}
```

---

### farmacias_simi3.png

**Tesseract**
- Tiempo: 0.33s
- Texto extraído:
```
DESCARGA LA APP

10 FARMACIAS SIMILARES Mis

Í . "LO MISMO PERO MAS BARATO"
o —_ _—————

ECJOJOJO OJO OO JOROO

O O
El /
DICLOFENACO DICLOFENACO75 MO DICLOFENACO DICLOFENACO 18 6R
100MG 20 TABLETAS IVITAMINAS 812 5 SODICO 75MG/3ML. SUSPENSION 120 ML
$200 $26.25 46400 $48.00 $20.00 $15.00 sesos $51.75
O Es O O O
Le a
|-20 E
%
[25%] 5%
DICLOFENACO KETOROLACO 30 M6 KETOROLACO 10 M6 KETOROLACO 30
MG/ML SOLUCION TABLETAS TO TABLETAS MG/1 ML SOLUCION
$25.00 $18.75 54400 $33.00

462.00 $39.75

$400 $30...
```

**Claude Vision**
- Tiempo: 4.61s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Similares",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "DICLOFENACO 100MG 20 TABLETAS",
      "precio_normal": 35.0,
      "precio_promo": 26.25,
      "unidad": "tab"
    },
    {
      "nombre": "DICLOFENACO 75 MG / VITAMINAS B12 5",
      "precio_normal": 64.0,
      "precio_promo": 48.0,
      "unidad": null
    },
    {
      "nombre": "DICLOFENACO SODICO 75MG/3ML",
      "precio_normal": 20.0,
      "precio_promo": 15.0,
      "unidad": "ml"
    },
    {
      "nombre": "DICLOFENACO .18 GR SUSPENSION 120 ML",
      "precio_normal": 69.0,
      "precio_promo": 51.75,
      "unidad": "ml"
    },
    {
      "nombre": "DICLOFENACO 1MG/ML SOLUCION",
      "precio_normal": 41.0,
      "precio_promo": 30.75,
      "unidad": "ml"
    },
    {
      "nombre": "KETOROLACO 30 MG TABLETAS",
      "precio_normal": 53.0,
      "precio_promo": 39.75,
      "unidad": "tab"
    },
    {
      "nombre": "KETOROLACO 10 MG 10 TABLETAS",
      "precio_normal": 25.0,
      "precio_promo": 18.75,
      "unidad": "tab"
    },
    {
      "nombre": "KETOROLACO 30 MG/1 ML SOLUCION",
      "precio_normal": 44.0,
      "precio_promo": 33.0,
      "unidad": "ml"
    }
  ]
}
```

---

### farmacias_simi4.png

**Tesseract**
- Tiempo: 0.25s
- Texto extraído:
```
“9” FARMACIAS SIMILARES a

"LO MISMO PERO MAS BARATO"

EJOJOLOOJOOIO0J0L - JOJOJO

O
$400 $30.75 453.00 $39.75 $25.00 $18.75 54400 $33.00
O O Ju) O
| a
E [25%]
43400 $25.50 41000 $59.25 401009 $23.25 $26.00 $27.00
```

**Claude Vision**
- Tiempo: 4.2s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "FARMACIAS SIMILARES",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "DICLOFENACO 1MG/ML SOLUCION",
      "precio_normal": 41.0,
      "precio_promo": 30.75,
      "unidad": "ml"
    },
    {
      "nombre": "KETOROLACO 30 MG TABLETAS",
      "precio_normal": 53.0,
      "precio_promo": 39.75,
      "unidad": "tab"
    },
    {
      "nombre": "KETOROLACO 10 MG 10 TABLETAS",
      "precio_normal": 25.0,
      "precio_promo": 18.75,
      "unidad": "tab"
    },
    {
      "nombre": "KETOROLACO 30 MG/1 ML SOLUCION",
      "precio_normal": 44.0,
      "precio_promo": 33.0,
      "unidad": "ml"
    },
    {
      "nombre": "IBUPROFENO CAPSULAS 600MG",
      "precio_normal": 34.0,
      "precio_promo": 25.5,
      "unidad": "cap"
    },
    {
      "nombre": "LINCOMICINA 600MG/2ML",
      "precio_normal": 79.0,
      "precio_promo": 59.25,
      "unidad": "ml"
    },
    {
      "nombre": "IBUPROFENO 800 MG 10 TABLETAS",
      "precio_normal": 31.0,
      "precio_promo": 23.25,
      "unidad": "tab"
    },
    {
      "nombre": "NAPROXENO SODICO/PARACETAMOL",
      "precio_normal": 36.0,
      "precio_promo": 27.0,
      "unidad": null
    }
  ]
}
```

---

### farmacia_1.jpg

**Tesseract**
- Tiempo: 0.17s
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
- Tiempo: 1.27s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": null,
  "ciudad": null,
  "vigencia": null,
  "medicamentos": []
}
```

---

### farmacia_10.png

**Tesseract**
- Tiempo: 0.37s
- Texto extraído:
```
FARMACIAS
. ñ o
Probemedic Busca por nombre o sustancia activa a A 20 l=]

Promociones

=>

te
4
te

LR

ANDANTOL
ANDANTOL JALEA 25 GR SOLUCION ANTISEPTICA MICRO- CANESTEN V CREMA 20 GR LOMECAN V 2% CREMA VAGINAL SOLUCIÓN MICRODACYN ANTI-
DACYN 60 120 ML 20 GR CEPTICO 60 ML
< CLOTRIMAZOL CLOTRIMAZOL >
520989 $184.00 52064 $194.31 459-009 $147.87 $359.09 $125.10 55372 $137.81
Agregar a carrito O Agregar a carrito O Agregar a carrito O Agregar a carrito O Agregar a carrito O
O)
```

**Claude Vision**
- Tiempo: 3.45s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Probemedic",
  "ciudad": "CDMX",
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "ANDANTOL JALEA 25 GR",
      "precio_normal": 200.0,
      "precio_promo": 184.0,
      "unidad": "gr"
    },
    {
      "nombre": "SOLUCION ANTISEPTICA MICRODACYN 60 120 ML",
      "precio_normal": 206.71,
      "precio_promo": 194.31,
      "unidad": "ml"
    },
    {
      "nombre": "CANESTEN V CREMA 20 GR",
      "precio_normal": 159.0,
      "precio_promo": 147.87,
      "unidad": "gr"
    },
    {
      "nombre": "LOMECAN V 2% CREMA VAGINAL 20 GR",
      "precio_normal": 139.0,
      "precio_promo": 125.1,
      "unidad": "gr"
    },
    {
      "nombre": "SOLUCIÓN MICRODACYN ANTI-SÉPTICO 60 ML",
      "precio_normal": 152.12,
      "precio_promo": 137.81,
      "unidad": "ml"
    }
  ]
}
```

---

### farmacia_11.png

**Tesseract**
- Tiempo: 0.37s
- Texto extraído:
```
FARMACIAS
busca por nombre o sustancia activa a A 20 y

Probemedic

Promociones

ka
15]

NEXCARE GENERICO
LAMISIL CREMA 1% 15 GR REPELENTE CORPORAL DE MOS-  REPELENTE CORPORAL DE MOS- CINTA MICROPORE NEXCARE LORATADINA 10 MG 20 TABLETA
QUITOS OFF 200 ML QUITOS OFF FAMILY SPRAY 177... BLANCO 2.5CMX5MTS 1 PIEZA
< LORATADINA >
$93.00 $83.69 $0440 $83.52 $76:62 $65.12 $5916 $53.24 $59.87 $15.90

Agregar a carrito O Agregar a carrito O Agregar a carrito O Agregar a carrito O Agregar a carrito O

2
```

**Claude Vision**
- Tiempo: 3.84s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Probemedic",
  "ciudad": "CDMX",
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "LAMISIL CREMA 1% 15 GR",
      "precio_normal": 93.0,
      "precio_promo": 83.69,
      "unidad": "gr"
    },
    {
      "nombre": "REPELENTE CORPORAL DE MOSQUITOS OFF 200 ML",
      "precio_normal": 104.4,
      "precio_promo": 83.52,
      "unidad": "ml"
    },
    {
      "nombre": "REPELENTE CORPORAL DE MOSQUITOS OFF FAMILY SPRAY 177 ML",
      "precio_normal": 76.62,
      "precio_promo": 65.12,
      "unidad": "ml"
    },
    {
      "nombre": "CINTA MICROPORE NEXCARE BLANCO 2.5CMX5MTS 1 PIEZA",
      "precio_normal": 59.16,
      "precio_promo": 53.24,
      "unidad": null
    },
    {
      "nombre": "LORATADINA 10 MG 20 TABLETA",
      "precio_normal": 19.87,
      "precio_promo": 15.9,
      "unidad": "tab"
    }
  ]
}
```

---

### farmacia_12.png

**Tesseract**
- Tiempo: 0.4s
- Texto extraído:
```
Farmacias dl

Te queremos. bien.

REFLUJO ME A

Filtros rápidos “Resultados (7858) organizar por: | Máspopulres y

9 Enviosncomin

y Promaciones ES MS

EL

EsccOne20 Unides 10m AopanGelOr120 sobres meprazo20 mg rato cápsulas 2

 Requierereceta Caer del Aroro

$66 1.5000 $283.

oe $149.00

Marca -

Osa 1
O amoo 1

DO arasaciar 2

O aseorr n

di AE

"Neural Solcióninyctante2 pz Alca Setter Anto del Malestar Esto inaveto Dimeticona16 cápauas
” maca y Balorde Gabeza Esa conté. RO

Precio -

5 — 08

...
```

**Claude Vision**
- Tiempo: 4.12s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias del Ahorro",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Lisora Oral 20 unidades 10 ml",
      "precio_normal": 661.05,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "Riopan Gel Oral 20 sobres",
      "precio_normal": 283.0,
      "precio_promo": null,
      "unidad": "sob"
    },
    {
      "nombre": "Omeprazol 20 mg Oral 60 cápsulas 2 Agio Marca del Ahorro",
      "precio_normal": 149.9,
      "precio_promo": null,
      "unidad": "cap"
    },
    {
      "nombre": "Neuralin Solución Inyectable 2 ml",
      "precio_normal": 151.2,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "Alka Seltzer Alivio del Malestar Estomacal y Dolor de Cabeza Caja con 12",
      "precio_normal": 39.6,
      "precio_promo": null,
      "unidad": "tab"
    },
    {
      "nombre": "Pinavério Omnicromtica 16 cápsulas Marca del Ahorro",
      "precio_normal": 146.9,
      "precio_promo": null,
      "unidad": "cap"
    }
  ]
}
```

---

### farmacia_13.png

**Tesseract**
- Tiempo: 0.44s
- Texto extraído:
```
FARMACIAS GUADALAJARA

up

Farmacia Der

Q Busca tus productos

Los más vendidos

Q Y

h
mounjaro*
tinepatida
Solución

Inpec

pun o

In.

$2,296.50

$1,722.37
MOUNJARO

Mounjaro 5mg/0.5ml
Solución Inyectable, Frasco
ámpula de dosis única.

Epia

$5,900.55

$3,149.00

OZEMPIC

Ozempic 1.34mg/ml Solución
Inyectable Pluma
Precargada, 1.5 ml.

Ofertas Ayuda

Libertri

1 mare
)

|! cc pen
a!

$657.69
LIBERTRIM

Libertrim Alfa
200mg/75mg/45mg, 24
Comprimidos.

$203.00

$140.07

ASPIRINA

Aspirina Pro...
```

**Claude Vision**
- Tiempo: 3.57s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Guadalajara",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Mounjaro 5mg/0.5ml",
      "precio_normal": 2296.5,
      "precio_promo": 1722.37,
      "unidad": "ml"
    },
    {
      "nombre": "Ozempic 1.34mg/ml Solución Inyectable Pluma",
      "precio_normal": 5900.55,
      "precio_promo": 3149.0,
      "unidad": "ml"
    },
    {
      "nombre": "Libertrim Alfa 200mg/75mg/45mg",
      "precio_normal": 1004.1,
      "precio_promo": 657.69,
      "unidad": null
    },
    {
      "nombre": "Aspirina Protect 100 mg",
      "precio_normal": 203.09,
      "precio_promo": 140.07,
      "unidad": null
    },
    {
      "nombre": "Wegovy 1mg/dosis Solución Inyectable",
      "precio_normal": 8004.8,
      "precio_promo": 3940.0,
      "unidad": "ml"
    }
  ]
}
```

---

### farmacia_14.png

**Tesseract**
- Tiempo: 0.48s
- Texto extraído:
```
Descarga la App móvil de Farmacias Guadalajara y realiza tus pedidos.

FARMACIAS GUADALAJARA Q Busca tus productos O Agregar dirección — Inicia sesión 4 Favoritos Ped

Farmacia Ofertas

Los más vendidos < >
Y) Y) o Y) Y) o Y) o >
¡| SILDENAFIL | b E | |
ÚN puamatiros comenta da "A hb.

a

o) Ey

$494.00 $26? $5,900.55 $8,004.89 $4
$340.86 $129.03 $2,900.00 $691.20 $4,280.00 $:
ASPIRINA PHARMALIFE WEGOVY VESSEL DUE OZEMPIC wi
Aspirina Protect 100 mg, 84 Pack Sildenafil 100 mg, 2 Wegovy 0.5mg/dosi...
```

**Claude Vision**
- Tiempo: 4.35s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Guadalajara",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "ASPIRINA Aspirina Protect 100 mg, 84 Tabletas",
      "precio_normal": 494.0,
      "precio_promo": 340.86,
      "unidad": "tab"
    },
    {
      "nombre": "PHARMALIFE Pack Sildenafil 100 mg, 2 Cajas con 8 Tabletas c/u Pharmalife",
      "precio_normal": 1722.67,
      "precio_promo": 129.03,
      "unidad": "tab"
    },
    {
      "nombre": "WEGOVY Wegovy 0.5mg/dosis 1.34mg/ml Solución Inyectable, 1 Pluma",
      "precio_normal": 5900.55,
      "precio_promo": 2900.0,
      "unidad": "ml"
    },
    {
      "nombre": "VESSEL DUE Vessel Due F 250LRU, 50 Cápsulas",
      "precio_normal": 960.0,
      "precio_promo": 691.2,
      "unidad": null
    },
    {
      "nombre": "OZEMPIC Ozempic 1.34mg/ml Solución Inyectable Pluma Precargada, 3 ml",
      "precio_normal": 8004.8,
      "precio_promo": 4280.0,
      "unidad": "ml"
    }
  ]
}
```

---

### farmacia_15.png

**Tesseract**
- Tiempo: 0.41s
- Texto extraído:
```
¡Envíos en 120 minutos! Haz tu pedido con hasta 6 Meses Sin Intereses

FARMACIAS GUADALAJARA Q Busca tus productos O Agregar dirección Inicia sesión  G Favoritos ed

Farmacia Ofertas

Los más vendidos < >

>
Cléarblue 5
Ca cn ti AYBELSUS* En E 3
Semaghutida 9
Brinteli<10mg tu 5
Tabletas z
Vortioxetina
ac cc
$2,652.00 $22 $499.87 $2
$109.51 $1,737.06 $2,172.43 $207.89 $349.91 $
CLEARBLUE BRINTELLIX RYBELSUS CLEARBLUE HISTOFIL LE
Clearblue Prueba de Brintellix 10 mg, 28 Tabletas. Rybelsus 3 mg, 30...
```

**Claude Vision**
- Tiempo: 3.35s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Guadalajara",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "CLEARBLUE Clearblue Prueba de Embarazo Plus, 1 Unidad.",
      "precio_normal": 184.23,
      "precio_promo": 109.51,
      "unidad": null
    },
    {
      "nombre": "BRINTELLIX Brintellix 10 mg, 28 Tabletas.",
      "precio_normal": 2652.0,
      "precio_promo": 1737.06,
      "unidad": "tab"
    },
    {
      "nombre": "RYBELSUS Rybelsus 3 mg, 30 Tabletas.",
      "precio_normal": 3272.72,
      "precio_promo": 2172.43,
      "unidad": "tab"
    },
    {
      "nombre": "CLEARBLUE Clearblue Prueba de Embarazo Digital, 1 Unidad.",
      "precio_normal": 389.46,
      "precio_promo": 207.89,
      "unidad": null
    },
    {
      "nombre": "HISTOFIL Histofil 4000UI, 60 Tabletas.",
      "precio_normal": 499.87,
      "precio_promo": 349.91,
      "unidad": "tab"
    }
  ]
}
```

---

### farmacia_2.jpg

**Tesseract**
- Tiempo: 0.29s
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
- Tiempo: 2.69s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias del Ahorro",
  "ciudad": null,
  "vigencia": "2024-06-29",
  "medicamentos": [
    {
      "nombre": "LA ROCHE-POSAY HYALU B5 CREME SURAC",
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
      "nombre": "PROTECTOR SOLAR SPF 50",
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
- Tiempo: 0.12s
- Texto extraído:
```

```

**Claude Vision**
- Tiempo: 4.42s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": null,
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "DETERGENTES BOLD",
      "precio_normal": 23.99,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "LIMPIADORAS ASKI LIMÓN",
      "precio_normal": null,
      "precio_promo": 25.0,
      "unidad": "450 ml"
    },
    {
      "nombre": "AGUA OXIGENADA ZAFRANIL",
      "precio_normal": null,
      "precio_promo": 25.0,
      "unidad": "250 ml"
    },
    {
      "nombre": "JARRÓN DE LAVANDERÍA FUERZAMAX",
      "precio_normal": null,
      "precio_promo": 17.99,
      "unidad": "350 g"
    },
    {
      "nombre": "LIMPIADORAS AMARILLO",
      "precio_normal": null,
      "precio_promo": 11.99,
      "unidad": "1 L"
    },
    {
      "nombre": "DETERGENTES ACE Y ARIEL",
      "precio_normal": null,
      "precio_promo": 35.0,
      "unidad": null
    },
    {
      "nombre": "LAMATRIXES SALVO LIMÓN",
      "precio_normal": null,
      "precio_promo": 50.0,
      "unidad": "500 ml"
    },
    {
      "nombre": "SUAVIZANTES BONY BLUE",
      "precio_normal": null,
      "precio_promo": 17.99,
      "unidad": "850 ml"
    },
    {
      "nombre": "DETERGENTE FROG",
      "precio_normal": null,
      "precio_promo": 35.0,
      "unidad": null
    },
    {
      "nombre": "HIGIENICOS GRASOL Y LINNETTE",
      "precio_normal": null,
      "precio_promo": 25.0,
      "unidad": null
    }
  ]
}
```

---

### farmacia_4.jpg

**Tesseract**
- Tiempo: 0.11s
- Texto extraído:
```

```

**Claude Vision**
- Tiempo: 1.7s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Más Farma",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Supradynes",
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
- Tiempo: 0.25s
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
- Tiempo: 2.59s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmatodo",
  "ciudad": null,
  "vigencia": "2025-05-31",
  "medicamentos": [
    {
      "nombre": "Nivea crema corporal Soft Milk variedad 400 ml",
      "precio_normal": 90.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "Nivea crema corporal Express Hydration variedad 400 ml",
      "precio_normal": 90.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "Nivea crema corporal Milk Nutritiva variedad 400 ml",
      "precio_normal": 90.0,
      "precio_promo": null,
      "unidad": "ml"
    }
  ]
}
```

---

### farmacia_6.png

**Tesseract**
- Tiempo: 0.33s
- Texto extraído:
```
Fr beñavides

benavides Acumula puntos * en todas tus compras

recompensas n
y recibe cupones de descuento”

LibertrimAlfa )

3x2

misma presentación

Apsulas ou Bu,

Temprafen Libertrim Alfa 2 Aa
400 me 200/75/45 mg enyataos
<h0 Caps. </24comps. Nyatabs

Lleva

1con 20% e CAB
vÉIZ9 30% MN
25259 ML misma presentación 3 Ki CAB y -

= 2x
2 o ames 2/30 tabs. 52,599

Pharmaton
Complete
e/30tabo.
```

**Claude Vision**
- Tiempo: 3.69s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Benavides",
  "ciudad": null,
  "vigencia": "2026-07-31",
  "medicamentos": [
    {
      "nombre": "Temprafen",
      "precio_normal": 79.0,
      "precio_promo": null,
      "unidad": "400mg c/10 caps"
    },
    {
      "nombre": "Libertrim Alfa",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": "200/75/45mg c/24 comps"
    },
    {
      "nombre": "Viagra",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": "100mg c/1 y 4 tabs"
    },
    {
      "nombre": "Pharmaton Complete",
      "precio_normal": 139.0,
      "precio_promo": 259.0,
      "unidad": "c/30 tabs"
    },
    {
      "nombre": "Sinuberases Colitis",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": "4 blis c/20 amps y 2 filtros ufc c/10 amps"
    },
    {
      "nombre": "Ki-Cab",
      "precio_normal": 2599.0,
      "precio_promo": null,
      "unidad": "50mg c/30 tabs"
    }
  ]
}
```

---

### farmacia_7.png

**Tesseract**
- Tiempo: 0.21s
- Texto extraído:
```
GUARDIANES DEL

VERINO SALUDABLE

descuento

$39... $76 2xs30 | $109.

ocomPRA, coma

Farmacias del
VO aorro

To queremos... bien.

Siempre mmm

beneficios
contu
```

**Claude Vision**
- Tiempo: 2.06s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias del Ahorro",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Alka-Seltzer",
      "precio_normal": 39.0,
      "precio_promo": 75.0,
      "unidad": null
    },
    {
      "nombre": "Advil",
      "precio_normal": 76.0,
      "precio_promo": 148.0,
      "unidad": null
    },
    {
      "nombre": "Electrolitos Ordes Marca del Ahorro",
      "precio_normal": 30.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Flanax",
      "precio_normal": 109.0,
      "precio_promo": 199.0,
      "unidad": null
    }
  ]
}
```

---

### farmacia_8.png

**Tesseract**
- Tiempo: 0.25s
- Texto extraído:
```
0v

Vive sin
dolor.

SACO Lom

(2) Todo desde la App con e

DE DESCUENTO

DEDESCUENTO

pira -
LY
Alliviax Eo

pc?

utiliza tu BR

AHORRA

15%

DEDESCUENTO

20%

DE DESCUENTO

A)

A
utiliza tu BA 2
```

**Claude Vision**
- Tiempo: 5.24s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "A+",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Syncol Maz",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Kateo Regular",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Nikzon",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Buscapina Fem",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Bio Electra",
      "precio_normal": 169.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Voltaren Emulgel",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Advil",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Meloral",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Alliviax, All-Triple",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Graneodín B",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Vick Drops",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Vick Vaporub",
      "precio_normal": 175.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Stérimar",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Allegra",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Theraflu",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Clarityne-D",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "X-TRID",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Reddy",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    }
  ]
}
```

---

### farmacia_9.png

**Tesseract**
- Tiempo: 0.33s
- Texto extraído:
```
(y

EXCLUSIVO EN: 2b%
fa Farmacias el o
e Ahorro Peso

Te quetemos.. bien.

NT
NUEVO SÉRUM Y

Actine

VITAMINA de A ll = Wi

DE DESCUENTO

REDUCCIÓN DE LAS
MARCAS POST ACNÉ:

MN > Ñ en tu vibe

A " 3
Pago de servicios y tiempo aire Utiliza tu (2) Medicamentos Marca Farmacia del Ahorro uttiza tu BA
```

**Claude Vision**
- Tiempo: 5.57s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias del Ahorro",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Electrolals",
      "precio_normal": 46.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Electrolals",
      "precio_normal": 66.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Suerex",
      "precio_normal": 40.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Pedialyte",
      "precio_normal": 66.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Suplemento alimenticio Marca del Ahorro",
      "precio_normal": 120.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Ensure Advance, Pedisure",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Glucerna, Ensure",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Casec",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "First Response, Gracia",
      "precio_normal": 72.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Just Ask",
      "precio_normal": 134.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Canesten V",
      "precio_normal": 145.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Canesten V",
      "precio_normal": 145.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Lomecan V",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Replens",
      "precio_normal": 129.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Unesia",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Nailex",
      "precio_normal": null,
      "precio_promo": null,
      "unidad": null
    }
  ]
}
```

---

### farmacia_similares.png

**Tesseract**
- Tiempo: 0.35s
- Texto extraído:
```
” FARMACIAS SIMILARES g£53>

"LO MISMO PERO MAS BARATO"

AM tot ¿Qué estás buscando? Q

CATEGORÍA

ANTIBIÓTICO

MEDICAMENTOS ÉTICOS o As o

ANTIHIPERTENSIVO

FUNCIONAMIENTO

GASTROINTESTINAL

ANTIINFLAMATORIO Pas

DIABETES —

5% 5
ANALGÉSICOS EJ
APARATO RESPIRATORIO AMOXICILINA / AMOXICILINA / AMOXICILINA / AMOXICILINA /
ACIDO ACIDO ACIDO ACIDO
REQUIERE RECETA
A
si
NO $99.00 $74.25 $95.00 $71.25 $6400 $48.00 $04.00 $48.00 (O)

RANGOS DE PRECIO

$ 5.00 $ 2,700.0 On On On On
```

**Claude Vision**
- Tiempo: 2.15s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Similares",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "AMOXICILINA / ACIDO",
      "precio_normal": 99.0,
      "precio_promo": 74.25,
      "unidad": null
    },
    {
      "nombre": "AMOXICILINA / ACIDO",
      "precio_normal": 95.0,
      "precio_promo": 71.25,
      "unidad": null
    },
    {
      "nombre": "AMOXICILINA / ACIDO",
      "precio_normal": 64.0,
      "precio_promo": 48.0,
      "unidad": null
    },
    {
      "nombre": "AMOXICILINA / ACIDO",
      "precio_normal": 64.0,
      "precio_promo": 48.0,
      "unidad": null
    }
  ]
}
```

---

### masfarma1.png

**Tesseract**
- Tiempo: 0.23s
- Texto extraído:
```
En MASFARMA
¡Ven por más!

Lasa

Omeprazol

Tribedoce

Compuesto

8
```

**Claude Vision**
- Tiempo: 5.57s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Masfarma",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Proxalin Plus Paracetamol-Naproxeno",
      "precio_normal": 35.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Omeprazol",
      "precio_normal": 12.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Lactiv",
      "precio_normal": 11.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Sarox Omeprazol",
      "precio_normal": 11.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Gelmicin",
      "precio_normal": 20.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Mavidol SL",
      "precio_normal": 12.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Osidea Gel Oral Sildenafil",
      "precio_normal": 58.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Tribedoce Compuesto",
      "precio_normal": 41.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Popram Panflorgazol Tableta 40 mg",
      "precio_normal": 22.0,
      "precio_promo": null,
      "unidad": "tab"
    },
    {
      "nombre": "Tribedoce Compuesto",
      "precio_normal": 46.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Mavidol",
      "precio_normal": 9.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Ketorolaco",
      "precio_normal": 13.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Gelubrin 600 Ibuprofeno 600 mg",
      "precio_normal": 28.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Nesajar",
      "precio_normal": 137.0,
      "precio_promo": null,
      "unidad": null
    }
  ]
}
```

---

### masfarma2.png

**Tesseract**
- Tiempo: 0.23s
- Texto extraído:
```
FEn MASFARMA

¡Ven por más!

748 —
¡Promocionesiválidasjlos
```

**Claude Vision**
- Tiempo: 5.42s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Masfarma",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Nesajar",
      "precio_normal": 117.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Flausivier Diosmina, Hespericina",
      "precio_normal": 64.0,
      "precio_promo": null,
      "unidad": "tableta"
    },
    {
      "nombre": "Sarox Omeprazol",
      "precio_normal": 11.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Atorlip atorvastatina",
      "precio_normal": 46.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Metformina",
      "precio_normal": 18.0,
      "precio_promo": null,
      "unidad": "tableta 850 mg"
    },
    {
      "nombre": "Losartán",
      "precio_normal": 35.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Mavidol TR",
      "precio_normal": 39.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Guvatox",
      "precio_normal": 61.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Sanzadoll Duo Tramadol, Paracetamol",
      "precio_normal": 44.0,
      "precio_promo": null,
      "unidad": "tableta"
    },
    {
      "nombre": "Galaver Gel",
      "precio_normal": 70.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Barmicil",
      "precio_normal": 27.0,
      "precio_promo": null,
      "unidad": "40 g"
    },
    {
      "nombre": "Proxalin Plus",
      "precio_normal": 40.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Gimmix Ácido Hialurónico",
      "precio_normal": 119.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Archer Compuesto",
      "precio_normal": 41.0,
      "precio_promo": null,
      "unidad": null
    }
  ]
}
```

---

### masfarma3.png

**Tesseract**
- Tiempo: 0.23s
- Texto extraído:
```
fEn MASFARMA

¡Ven por más!

Dentro aot los
```

**Claude Vision**
- Tiempo: 6.23s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Masfarma",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "Proxalin Plus Paracetamol-Naproxano",
      "precio_normal": 35.0,
      "precio_promo": null,
      "unidad": "tab"
    },
    {
      "nombre": "Proxalin Plus",
      "precio_normal": 40.0,
      "precio_promo": null,
      "unidad": "tab"
    },
    {
      "nombre": "Tribedoce Compuesto",
      "precio_normal": 44.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Lactiv",
      "precio_normal": 11.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Gelmicin",
      "precio_normal": 20.0,
      "precio_promo": null,
      "unidad": "g"
    },
    {
      "nombre": "Dexametasona",
      "precio_normal": 10.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Amcef I.M. Cefotaxima",
      "precio_normal": 23.0,
      "precio_promo": null,
      "unidad": "g"
    },
    {
      "nombre": "Mavidol",
      "precio_normal": 8.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Osidea Gel Oral",
      "precio_normal": 58.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "Ketorolaco",
      "precio_normal": 13.0,
      "precio_promo": null,
      "unidad": "ml"
    },
    {
      "nombre": "Popram",
      "precio_normal": 23.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Trixona I.M. Ceftriaxona",
      "precio_normal": 23.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Sinkel Dexametasona",
      "precio_normal": 34.0,
      "precio_promo": null,
      "unidad": null
    },
    {
      "nombre": "Gelubrin 600",
      "precio_normal": 8.0,
      "precio_promo": null,
      "unidad": "mg"
    },
    {
      "nombre": "Ibuprofeno 600mg",
      "precio_normal": 25.0,
      "precio_promo": null,
      "unidad": "mg"
    }
  ]
}
```

---

### simi5.png

**Tesseract**
- Tiempo: 0.28s
- Texto extraído:
```
DESCARGA LA APP 4

% 1” FARMACIAS SIMILARES Mis

"LO MISMO PERO MAS BARATO"

0060600000000»

Comprar ahora Comprar ahora Comprar ahora Comprar ahora

Á
$20.00 $29.25 ó000s $149.25 $200 $15.75 $2200 $24.00
O O O
m/s
>
d000 $27.75 46oc0 $44.25 ás000 $59.25 $ss0s $42.00
```

**Claude Vision**
- Tiempo: 4.07s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "Farmacias Similares",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "LORATADINA 100MG/100ML",
      "precio_normal": 39.0,
      "precio_promo": 29.25,
      "unidad": "ml"
    },
    {
      "nombre": "FINASTERIDA 5 MG",
      "precio_normal": 199.0,
      "precio_promo": 149.25,
      "unidad": "tab"
    },
    {
      "nombre": "LORATADINA 100MG/100ML",
      "precio_normal": 21.0,
      "precio_promo": 15.75,
      "unidad": "ml"
    },
    {
      "nombre": "BETAMETASONA/G... 40GR CREMA",
      "precio_normal": 32.0,
      "precio_promo": 24.0,
      "unidad": "g"
    },
    {
      "nombre": "BETAMETASONA 8MG/2ML SOLUCION",
      "precio_normal": 37.0,
      "precio_promo": 27.75,
      "unidad": "ml"
    },
    {
      "nombre": "METRONIDAZOL / DIYODOHIDROXIQU...",
      "precio_normal": 59.0,
      "precio_promo": 44.25,
      "unidad": null
    },
    {
      "nombre": "BETAMETASONA 0.1% VALERATO",
      "precio_normal": 79.0,
      "precio_promo": 59.25,
      "unidad": null
    },
    {
      "nombre": "BETAMETASONA DE DIPROPIONATO /",
      "precio_normal": 56.0,
      "precio_promo": 42.0,
      "unidad": null
    }
  ]
}
```

---

### simi6.png

**Tesseract**
- Tiempo: 0.32s
- Texto extraído:
```
¡DESCARGA LA APP do.

po F

ARMACIAS SIMILARES ¿33

"LO MISMO PERO MAS BARATO"

2 <<< A

Pe $000

00606000000 SON

¡u)

¡u)

LEVONORGESTREL LEVONORGESTREL / TADALAFIL 20 MG 4 TADALAFIL SMG 14
1.5MG 1TABLETA ETINILESTRADIOL TABLETAS TABLETAS
secoo $48.75 das0o $32.25

sees $126.75 $22000 $171.75

¡u) ¡u) ¡u) ¡u)
= A a
TADALAFIL 20 MG 1 ATORVASTATINA 20 ATORVASTATINA 40 SALES DE POTASIO
TABLETA MG 10 TABLETAS MG 10 TABLETAS SOTABLETAS
47009 $59.25

$49.50 $neoo $87.00

$200 $99.00
```

**Claude Vision**
- Tiempo: 4.0s
- Éxito: ✅
- JSON:
```json
{
  "farmacia": "FARMACIAS SIMILARES",
  "ciudad": null,
  "vigencia": null,
  "medicamentos": [
    {
      "nombre": "LEVONORGESTREL 1.5 MG 1 TABLETA",
      "precio_normal": 65.0,
      "precio_promo": 48.75,
      "unidad": "tab"
    },
    {
      "nombre": "LEVONORGESTREL / ETINILESTRADIOL",
      "precio_normal": 43.0,
      "precio_promo": 32.25,
      "unidad": null
    },
    {
      "nombre": "TADALAFIL 20 MG 4 TABLETAS",
      "precio_normal": 169.0,
      "precio_promo": 126.75,
      "unidad": "tab"
    },
    {
      "nombre": "TADALAFIL 5MG 14 TABLETAS",
      "precio_normal": 229.0,
      "precio_promo": 171.75,
      "unidad": "tab"
    },
    {
      "nombre": "TADALAFIL 20 MG 1 TABLETA",
      "precio_normal": 79.0,
      "precio_promo": 59.25,
      "unidad": "tab"
    },
    {
      "nombre": "ATORVASTATINA 20 MG 10 TABLETAS",
      "precio_normal": 66.0,
      "precio_promo": 49.5,
      "unidad": "tab"
    },
    {
      "nombre": "ATORVASTATINA 40 MG 10 TABLETAS",
      "precio_normal": 116.0,
      "precio_promo": 87.0,
      "unidad": "tab"
    },
    {
      "nombre": "SALES DE POTASIO 50 TABLETAS",
      "precio_normal": 132.0,
      "precio_promo": 99.0,
      "unidad": "tab"
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
