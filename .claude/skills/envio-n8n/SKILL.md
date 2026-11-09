---
name: envio-n8n
description: Al final de una consulta de evento (ruta lead), monta los 15 campos del contrato de Ale y envía la consulta a n8n una sola vez con scripts/enviar_n8n.py, tapando los datos que tocan; después dice al cliente la frase que corresponde a la respuesta. También apunta cada conversación, vaya o no a n8n, en el registro anónimo. No pide datos ni consentimiento (eso es consentimiento), no puntúa ni promete plazos, y no se usa en tareas de desarrollo.
---

# Envío a n8n

Se aplica después de cualificador-leads y consentimiento. El contrato completo está en `KNOWLEDGE.md` §3.2. El envío y el registro los hace `scripts/enviar_n8n.py`; el LLM solo le pasa los datos de la conversación y dice la frase que el script devuelve.

## 1. Cuándo se envía
- Solo en una ruta `lead` (el router devuelve `a_n8n`), cuando `listo_para_enviar` es verdadero **y** el cliente ha respondido a la pregunta de privacidad.
- **Una sola vez por consulta.** El script no envía dos veces la misma conversación: si ya se envió, no hace nada.
- Si el cliente cierra el chat:
  - después de responder a la privacidad → se envía (si no contestó a la publicidad, `marketing_consent: no`);
  - antes de responder a la privacidad → no se envía; solo se apunta en el registro.
- Quejas, cambios de reserva, privacidad, petición de persona sin consulta y fuera de tema **no van a n8n**: solo se apuntan en el registro.

## 2. Qué datos se pasan al script
- Los datos de la consulta: tipo de evento, asistentes, espacio elegido o zona, fecha, presupuesto y necesidades, tal como los dijo el cliente.
- El nombre del espacio elegido va completo, como en el catálogo ("Llum del Poblenou", no "Llum"). Si no eligió, la zona que dijo. Si tampoco, vacío.
- La fecha solo como día exacto (AAAA-MM-DD). Si solo dijo el mes o "en primavera", la fecha va vacía: n8n la lee de la conversación.
- En `message`, lo que pide en sus palabras y **los escalados de la consulta** (descuento, catering, extras a medida, excepciones, permisos), cada uno en una frase: "Pide descuento." "Quiere terminar a las 02:00 en el Jardí."
- La conversación completa, una línea por turno con `Bot:` o `Client:`.
- Las respuestas de consentimiento: privacidad (sí / no / solo teléfono) y publicidad (sí / no / sin respuesta).
- Nunca la puntuación del cualificador (no existe) ni notas internas.

## 3. Qué se tapa (lo hace el script)
- **Siempre:** números de tarjeta, IBAN y DNI/NIE en la conversación y en `message`.
- **Sin "sí" a la privacidad** (dijo que no, retiró el permiso o solo dio teléfono):
  - `name`, `email`, `phone` y `company` van vacíos;
  - en la conversación se tapan su nombre, email, teléfono y empresa;
  - `gdpr_consent: no` y `marketing_consent: no`.
  - Por confirmar con Ale que n8n acepta este envío anónimo (KNOWLEDGE §3.2).

## 4. Qué dice el chatbot después
El script devuelve el resultado y la frase. Se dice tal cual, en el idioma del cliente, sin añadir plazos ni promesas.

| Resultado | Frase |
|---|---|
| 202 (o 202 SIMULADA) | "Gracias. El equipo se pondrá en contacto contigo en breve." |
| 403 / 404, o sin respuesta tras el reintento | "Gracias. El equipo contactará contigo igualmente." |
| Envío sin datos personales (privacidad "no" o solo teléfono) | Nada más: ya se dijo la frase de consentimiento §4. |

- Si el cliente eligió un espacio, se puede añadir: "Te contactará [comercial del espacio]." Si no, nada (guardrails, decisión 9).
- Nunca "tu reserva está confirmada" ni "te llamamos hoy".
- Después del envío, si el cliente sigue escribiendo, se le atiende con normalidad, pero no se vuelve a enviar. Si cambia un dato ("al final somos 150"): "Lo apunto para el comercial; te lo confirmará cuando te contacte." No se reenvía.

## 5. Registro anónimo de cada conversación
- Al final de **cada** conversación, vaya o no a n8n, el script añade una línea a `registros/conversaciones.jsonl`.
- Sin datos personales: nada de nombre, email, teléfono, empresa ni texto de la conversación.
- Campos: los de la §3.2 de KNOWLEDGE (registro anónimo). Sirven para el dashboard, que los junta con las hojas de Ale por `lead_id`.

## 6. Reglas que no se saltan
- La URL y la clave solo en variables de entorno (`N8N_WEBHOOK_URL`, `N8N_API_KEY`). Nunca en el código, el repositorio, el chat ni el navegador.
- Sin esas variables, el envío se simula (202 SIMULADA) con el mismo formato.
- En pruebas, solo datos sintéticos y los emails de prueba de Ale (`alejandro+ie007-xxx@alelabs.es`).

## 7. Ejemplos
- Cena para 80 en el Mirador el 12 de diciembre, presupuesto 6.000 €, "sí" a la privacidad, "no" a la publicidad → se envía con `preferred_location: "Mirador de Montjuïc"`, `event_date: "2026-12-12"`, `gdpr_consent: yes`, `marketing_consent: no` → 202 → "Gracias. El equipo se pondrá en contacto contigo en breve. Te contactará Marta Soler."
- Presentación para 120 "en marzo", sin espacio elegido, zona Poblenou → `preferred_location: "Poblenou"`, `event_date: ""` → 202 → "Gracias. El equipo se pondrá en contacto contigo en breve."
- Pide un 10 % de descuento durante la consulta → en `message`: "Pide descuento." Al cliente ya se le dijo que lo verá con el comercial (guardrails).
- "No" a la privacidad → se envía sin datos personales y con la conversación tapada; el chatbot no dice nada más.
- Escribe su tarjeta en el chat → en la conversación enviada sale `[tarjeta]`.
- Cierra el chat antes de la pregunta de privacidad → no se envía; línea en el registro con `enviado_n8n: no`.
- Queja por un evento pasado → no va a n8n; línea en el registro con ruta `incidencia`.
- Tras el envío: "¿Me lo podéis reenviar?" → "Ya está enviado; el equipo se pondrá en contacto contigo." No se reenvía.
