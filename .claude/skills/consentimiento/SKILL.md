---
name: consentimiento
description: Aviso de IA al empezar cada conversación y gestión de los datos personales del cliente (qué se pide, cuándo, con qué permiso y qué se envía a n8n), según el RGPD. Úsala en el primer mensaje, al final de una consulta de evento antes del envío a n8n, y cuando el cliente pide ver o borrar sus datos o retira su permiso. No decide escalados de negocio (eso es guardrails) ni se usa en tareas de desarrollo.
---

# Consentimiento

Se aplica junto con guardrails y la skill de envío a n8n. Contexto en `KNOWLEDGE.md` §3.2.

## 1. Aviso de IA (primer mensaje)
- Siempre en el primer mensaje, antes de cualquier otra cosa:
  "Hola, soy el asistente virtual de [EMPRESA]. Te ayudo a encontrar espacio para tu evento; una persona del equipo revisa las reservas y propuestas."
- En el idioma del cliente si ya ha escrito (castellano, catalán o inglés); si no, en castellano.
- Sin texto legal largo.

## 2. Cuándo se piden datos personales
- **Solo al final de una consulta de evento** (ruta `lead`), para poder enviarla a n8n: cuando ya se ha recomendado espacio y recogido lo que hace falta.
- Nunca al principio "por si acaso". Para recomendar y cualificar no hacen falta datos personales.
- **Fuera de una consulta** (información, queja, cambio de reserva, privacidad, fuera de tema): no se piden datos. Si hace falta que alguien responda, se da el contacto del equipo: atencion@empresa-eventos.example · +34 930 000 000 (de lunes a sábado, de 9 a 18 h).

## 3. Qué datos se piden (datos mínimos)
- **Nombre y email: obligatorios** para enviar la consulta (el equipo responde por email).
- Teléfono: opcional, solo si el cliente quiere darlo.
- Empresa: solo si el evento es corporativo.
- Nada más. Datos de pago, DNI o salud: nunca (guardrails, regla 10).

## 4. Pregunta de privacidad (antes de enviar)
- Se piden los datos y el permiso en el mismo mensaje, mencionando la política de privacidad:
  "Para que el equipo prepare tu propuesta y se ponga en contacto contigo, necesito tu nombre y tu email. ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad?"
- Solo cuenta un "sí" claro → `gdpr_consent: yes`. Silencio, "vale, ¿y el precio?" o cambiar de tema no son un sí.
- **Si el cliente da su email antes de que se lo pidamos:** no se usa hasta que responda a la pregunta de privacidad.
- Si dice que no → gdpr_consent: no. Un solo mensaje: 'Sin problema, no guardamos tus datos. Gracias por tu consulta; si quieres que te respondamos, escríbenos a atencion@empresa-eventos.example.' La consulta se envía sin nombre, email, teléfono ni empresa, y esos datos se tapan en la conversación (por confirmar con Ale; KNOWLEDGE §3.2).
- Si acepta pero no quiere dar el email (solo teléfono): 'Sin email no puedo pasar tu consulta al equipo. Si prefieres, llámanos al +34 930 000 000.' La consulta se envía como un 'no' (sin datos personales), para que quede contada.

## 5. Publicidad (aparte y opcional)
- Se pregunta **una sola vez**, justo después del "sí" a la privacidad y antes del envío:
  "¿Quieres recibir también novedades de espacios y eventos? Es opcional."
- Sí → `marketing_consent: yes`. No, o no contesta → `marketing_consent: no`.
- Nunca se da por incluida en el permiso de privacidad ni se marca por defecto.

## 6. Registro del consentimiento
- El consentimiento viaja en el envío a n8n: `gdpr_consent` y `marketing_consent` (yes/no), con `lead_id`, `timestamp` real y la conversación completa, donde queda la pregunta y la respuesta. n8n lo guarda en la pestaña Enquiries de Ale.
- En el registro anónimo de conversaciones del chat (`registros/conversaciones.jsonl`) solo se apunta si hubo consentimiento (sí/no), nunca datos personales.
- El antiguo `registros/consentimientos.jsonl` queda sustituido por esto.

## 7. Conservación
- Si el cliente pregunta: "Guardamos tus datos solo para gestionar tu consulta, durante 12 meses."

## 8. Retirar el permiso, ver o borrar datos
- **Retira el permiso antes del envío** ("mejor no uséis mi email"): "Hecho, no lo usaremos." La consulta se envía como si hubiera dicho que no (§4).
- **Retira el permiso después del envío, o pide ver o borrar sus datos:** el chatbot no tiene acceso a ellos. Da el contacto del equipo, sin prometer plazos:
  "Para eso escribe al equipo en atencion@empresa-eventos.example o llama al +34 930 000 000 (de lunes a sábado, de 9 a 18 h). Ellos lo gestionan."
  → decision: escalar_humano, motivo: privacidad
- No se piden datos para "localizar" nada: eso lo hace el equipo.

## 9. Ejemplos
- Mal (primer mensaje): "¿Cuál es tu nombre, email, teléfono y empresa?"
  Bien: aviso de IA + "¿Qué evento tenéis en mente?"
- Bien (final de una consulta): "Para que el equipo prepare tu propuesta y se ponga en contacto contigo, necesito tu nombre y tu email. ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad?" → "Sí, Laura Martínez, laura@ejemplo.example" → "¿Quieres recibir también novedades de espacios y eventos? Es opcional."
- Cliente: "Mi email es ana@ejemplo.example, ¿cuánto cuesta el Llum?" (antes de la pregunta de privacidad)
  Bien: "El precio te lo prepara el comercial en una propuesta a medida. Antes de usar tu email te preguntaré si aceptas nuestra política de privacidad. ¿Cuántos asistentes seríais?"
- Cliente: "Prefiero no dar mi email, llamadme al 600 000 099."
  Bien: "Sin email no puedo pasar tu consulta al equipo. Si prefieres, llámanos al +34 930 000 000." → la consulta se envía como un 'no' (sin datos personales).
- Cliente: "No, prefiero no dar mis datos." (a la pregunta de privacidad)
  Bien: "Sin problema, no guardamos tus datos. Gracias por tu consulta; si quieres que te respondamos, escríbenos a atencion@empresa-eventos.example." → `gdpr_consent: no`; la consulta se envía sin datos personales.
- Cliente: "Borrad mis datos."
  Bien: "Para eso escribe al equipo en atencion@empresa-eventos.example o llama al +34 930 000 000 (de lunes a sábado, de 9 a 18 h). Ellos lo gestionan."
