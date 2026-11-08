---
name: cualificador-leads
description: Durante una consulta de evento, decide qué datos faltan y qué preguntar (tipo de evento, asistentes, espacio o zona, fecha, presupuesto y necesidades) para que la consulta llegue completa a n8n. Lo decide scripts/datos_consulta.py; el LLM solo pregunta y traduce las frases del cliente a niveles con la tabla de la §3. No puntúa: la puntuación oficial la hace n8n (KNOWLEDGE §3.2). No se usa para recomendar espacios, dar precios ni confirmar disponibilidad.
---

# Cualificador de leads

Se aplica junto con guardrails, recomendador-espacios, consentimiento y la skill de envío a n8n. Contexto en `KNOWLEDGE.md` §3.2.

## 1. Para qué sirve
Que la consulta llegue a n8n con lo que su flujo necesita:
- **Zona o espacio elegido**: sin ella, n8n no asigna espacio ni envía el email automático.
- **Fecha**: sin fecha (o con fecha pasada), tampoco hay email automático.
- **Presupuesto**: sin él, n8n nunca califica el lead como fuerte.
El cualificador **no puntúa ni decide** nada sobre el lead: solo qué preguntar.

## 2. Qué datos recoge, en este orden
| # | Dato | Tipo | Campo del envío |
|---|---|---|---|
| 1 | Tipo de evento | imprescindible | `event_type` |
| 2 | Asistentes | imprescindible | `guests` |
| 3 | Espacio elegido o, si no, zona | imprescindible | `preferred_location` |
| 4 | Fecha, aunque sea aproximada (día, mes o temporada) | imprescindible | `event_date` (solo si hay día exacto) |
| 5 | Día exacto, si solo dio el mes o la temporada ("¿Tenéis ya un día concreto, o al menos el mes?") | recomendable | `event_date` |
| 6 | Presupuesto | recomendable | `budget_eur` |
| 7 | Necesidades (catering, audiovisuales, extras…) | recomendable | `message` |

- La empresa, el nombre y el email los pide la skill consentimiento, no esta.
- El espacio sale del recomendador: después de las tarjetas se pregunta "¿Cuál os encaja más?". Si no quiere elegir, basta con la zona.

## 3. De frases a niveles (tabla fija)
| Dato | Frases | Nivel |
|---|---|---|
| Fecha | "el 14 de marzo", "el sábado 6 de junio" | día exacto |
| Fecha | "en marzo", "la segunda quincena de mayo", "entre el 10 y el 20" | mes o rango |
| Fecha | "en primavera", "el año que viene" | temporada |
| Asistentes / presupuesto | "120", "6.000 €", "unos 100", "entre 2.000 y 3.000" | dado (n8n acepta números y rangos) |
| Cualquiera | "no lo sé", "aún no", "ya veremos" | no lo sabe |

## 4. La decisión la toma el script
Se ejecuta `scripts/datos_consulta.py` con lo que se sabe y con lo que ya se ha preguntado. Devuelve:
- los datos que faltan, en el orden de la §2;
- **las siguientes preguntas** (máximo dos, las dos primeras que falten);
- `listo_para_enviar`: verdadero cuando cada dato está dado **o ya se preguntó una vez**.

Reglas:
- **Cada dato se pregunta una sola vez.** Si el cliente no lo sabe o no contesta, no se insiste: cuenta como preguntado.
- Una o dos preguntas por mensaje, intercaladas con la conversación. Nunca un cuestionario seguido.
- Cuando `listo_para_enviar` es verdadero → skill consentimiento (§4, pregunta de privacidad) → skill de envío a n8n.

## 5. Escalados dentro de una consulta
Descuentos, catering o extras a medida, excepciones de horario o aforo, permisos: no se escalan aparte. Se apuntan para el campo `message` en una frase ("Pide un 20 % de descuento"; "Quiere música hasta las 4") y se sigue con la consulta (KNOWLEDGE §3.2, decisión 6). Al cliente: "Lo verás con el comercial cuando te contacte."

## 6. Ejemplos
- "Queremos hacer algo para la empresa." → faltan tipo y asistentes → "¿Qué tipo de evento tenéis en mente y para cuántas personas?"
- "Cena para 120 en marzo; nos gusta el Llum." → faltan día exacto y presupuesto → "¿Tenéis ya un día concreto? ¿Y un presupuesto aproximado?"
- El cliente contesta "Aún no sabemos ni el día ni el presupuesto." → se han preguntado una vez → falta necesidades → "¿Necesitaréis algo especial, como catering o audiovisuales?" → después, `listo_para_enviar`.
- Mal: "Tu lead tiene 80 puntos." El cualificador ya no puntúa.
- Mal: preguntar el presupuesto por segunda vez después de "aún no lo sabemos".
