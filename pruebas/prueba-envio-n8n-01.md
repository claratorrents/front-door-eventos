# Prueba envio-n8n 01 · Ruta estrella completa

Fecha: 9 de noviembre de 2026
Punto 8 del paso 2 de la integración: prueba de punta a punta con el envío simulado.
Skills: router-intenciones, guardrails, consentimiento, recomendador-espacios, media-espacios, cualificador-leads y envio-n8n, tal como están en el commit de esta prueba.
Scripts: `router.py`, `recomendar.py`, `datos_consulta.py` y `enviar_n8n.py`, ejecutados de verdad en cada turno.
Método:
- **Papeles:** yo hago de chatbot siguiendo las skills y de cliente sintético, con el email de prueba de Ale `alejandro+ie007-c99@alelabs.es` y el nombre inventado "Marina Prueba".
- **Envío:** SIMULADO, sin `N8N_WEBHOOK_URL` ni `N8N_API_KEY` en el entorno.
- **Registro:** se ha escrito en un archivo temporal, no en `registros/` del proyecto.
- **Fecha de referencia:** hoy, 9/11/2026.

## Conversación principal

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C0 | Hola. | Solo un saludo: no se llama al router (router §4) |
| B0 | Hola, soy el asistente virtual de [EMPRESA]. Te ayudo a encontrar espacio para tu evento; una persona del equipo revisa las reservas y propuestas. ¿Qué evento tenéis en mente? | Aviso de IA (consentimiento §1) |
| C1 | Queremos una presentación de producto para unas 120 personas en enero, por la zona de Poblenou. | `router.py nuevo_evento` → skills guardrails, recomendador, cualificador · si toca media, consentimiento, **envio-n8n** · `a_n8n` **true** · ruta `lead` |
| | | Presentación → `theater` (recomendador §1). `recomendar.py --asistentes 120 --disposicion theater` → Mirador `comodo` (75 %, foto-03), Llum `comodo` (60 %, foto-02), Fòrum `al_limite` (92 %, foto-01). Sin `--dias` (solo se sabe el mes) ni hora de fin |
| | | `datos_consulta.py --tipo "presentación de producto" --asistentes "unas 120" --zona Poblenou --fecha mes` → faltan [dia_exacto, presupuesto, necesidades]; la zona cuenta como dada |
| B1 | Para una presentación lo normal es formato teatro; ¿os encaja?<br>**Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Tiene sitio para 160 personas en formato teatro. *[imagen: mirador-montjuic-foto-03, Imagen ilustrativa]*<br>**Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 200 personas en teatro. Encaja para una presentación de producto. *[imagen: llum-poblenou-foto-02, Imagen ilustrativa]*<br>**Fòrum de les Corts.** Sala ejecutiva y polivalente junto a los principales centros de negocio. Hasta 130 personas en teatro. Cabe justo; si podéis ser alguno más, mejor el Mirador. *[imagen: forum-les-corts-foto-01, Imagen ilustrativa]*<br>¿Cuál os encaja más? También puedo enseñaros el plano o el recorrido 360°. | Orden y fotos del script. "Por qué encaja" solo en el Llum: "presentacion" solo está en sus `event_types`. Dos preguntas: el formato y la pregunta final del recomendador. Las del cualificador esperan |
| C2 | Sí, teatro. Nos quedamos con el Llum. | Elección → `preferred_location` "Llum del Poblenou" (recomendador §3) |
| | | `datos_consulta.py … --espacio "Llum del Poblenou"` → preguntas [dia_exacto, presupuesto] |
| B2 | Perfecto, el Llum del Poblenou. ¿Tenéis ya un día concreto? ¿Y un presupuesto aproximado? | Las dos preguntas del script |
| C3 | ¿Tiene parking? | Información dentro de un evento: se responde y se sigue con `nuevo_evento` (router §4). No contesta al día ni al presupuesto → **cuentan como preguntados** (cualificador §4) |
| | | `datos_consulta.py … --preguntados dia_exacto,presupuesto` → preguntas [necesidades] |
| B3 | El Llum tiene carga y descarga en puerta, y un parking público a 150 m. ¿Necesitaréis algo especial, como catering o audiovisuales? | Parking con el dato del espacio, "Carga y descarga en puerta; parking público a 150m" (guardrails, regla 7) |
| C4 | ¿Nos podéis hacer un 10 % de descuento? | Guardrails, reglas 3 y 11 → `escalar_comercial`, `descuento` · al message: "Pide un 10 % de descuento". Necesidades sin contestar → cuenta como preguntado |
| | | `datos_consulta.py … --preguntados dia_exacto,presupuesto,necesidades` → faltan [] · **`listo_para_enviar` true** → consentimiento §4 |
| B4 | Los descuentos los valora el comercial; lo verás con él cuando te contacte. Para que el equipo prepare tu propuesta y se ponga en contacto contigo, necesito tu nombre y tu email. ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad? | **Llega a la pregunta de privacidad antes de tener el día, el presupuesto y las necesidades** (fallo 2) |
| C5 | El día sería el 20 de enero de 2027. | No responde a la privacidad: no es un "sí" (consentimiento §4). Día exacto → **se revalida** (recomendador §1) |
| | | `recomendar.py --validar sp-llum-poblenou --asistentes 120 --disposicion theater --dias 72` → **encaja**, sin motivos, `avisos_zona` [], foto llum-poblenou-foto-02 (el Llum pide 7 días; faltan 72) |
| B5 | Para el 20 de enero, el Llum del Poblenou llega bien. | Sin pregunta: la de privacidad sigue pendiente |
| C6 | Tenemos un presupuesto de 8.000 € y necesitamos pantalla y sonido. | Presupuesto y necesidades: dados (se envían aunque ya contaran como preguntados) |
| B6 | Apuntado. Para que el equipo prepare tu propuesta y se ponga en contacto contigo, necesito tu nombre y tu email. ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad? | Se repite la pregunta de privacidad. La skill no dice si se puede repetir (fallo 3) |
| C7 | Sí, acepto. Me llamo Marina Prueba y mi email es alejandro+ie007-c99@alelabs.es. | "Sí" claro → `gdpr_consent: yes` |
| B7 | ¿Quieres recibir también novedades de espacios y eventos? Es opcional. | Publicidad, una vez, después del "sí" (consentimiento §5) |
| C8 | No, gracias. | `marketing_consent: no` → envio-n8n |
| | | `enviar_n8n.py` → `enviado` **simulado** · `respuesta` **202_simulada** · `lead_id` CB-20261109-103942-Q78K · `frase` "Gracias. El equipo se pondrá en contacto contigo en breve." |
| B8 | Gracias. El equipo se pondrá en contacto contigo en breve. | Frase de la skill envio-n8n §4, tal cual |

### Payload enviado (simulado)
```json
{
  "lead_id": "CB-20261109-103942-Q78K",
  "timestamp": "2026-11-09T10:39:42Z",
  "name": "Marina Prueba",
  "email": "alejandro+ie007-c99@alelabs.es",
  "company": "",
  "phone": "",
  "preferred_location": "Llum del Poblenou",
  "event_type": "presentación de producto",
  "event_date": "2027-01-20",
  "guests": "unas 120",
  "budget_eur": "8.000 €",
  "message": "Necesitan pantalla y sonido. Pide un 10 % de descuento.",
  "conversation": "Client: Hola.\nBot: Hola, soy el asistente virtual de [EMPRESA]. …\nClient: Queremos una presentación de producto para unas 120 personas en enero, por la zona de Poblenou.\n…\nClient: Sí, acepto. Me llamo Marina Prueba y mi email es alejandro+ie007-c99@alelabs.es.\nBot: ¿Quieres recibir también novedades de espacios y eventos? Es opcional.\nClient: No, gracias.",
  "gdpr_consent": "yes",
  "marketing_consent": "no"
}
```
`conversation` lleva los 17 turnos completos (C0 a C8), uno por línea; aquí se abrevia.
- **`espacio_elegido`:** se pasó como "Llum" y el script lo normalizó a "Llum del Poblenou".
- **`company`:** va vacío porque el cliente no dijo empresa y nadie se la pidió (comentario 4).

### Línea del registro anónimo
```json
{"id_conversacion": "conv-ruta-estrella-01", "fecha_hora": "2026-11-09T10:39:42Z", "idioma": "es", "ruta": "lead", "rutas_adicionales": [], "decision": "escalar_comercial", "motivo_escalado": "descuento", "espacio_elegido": "Llum del Poblenou", "enviado_n8n": "simulado", "respuesta_n8n": "202_simulada", "lead_id": "CB-20261109-103942-Q78K", "consentimiento_datos": "si", "consentimiento_publicidad": "no", "resuelto_sin_humano": "no"}
```

**Repetición:** la misma conversación pasada otra vez a `enviar_n8n.py` → `ya_enviado: true`, el mismo `lead_id` y la frase vacía. No se reenvía ni se añade otra línea al registro.

## Variante (a): "no" a la privacidad

Igual hasta B6. Después:

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C7a | No, prefiero no dar mis datos. | `gdpr_consent: no` |
| B7a | Sin problema, no guardamos tus datos. Gracias por tu consulta; si quieres que te respondamos, escríbenos a atencion@empresa-eventos.example. | Frase de consentimiento §4, un solo mensaje. No se pregunta la publicidad |
| | | `enviar_n8n.py` → `enviado` simulado · `respuesta` 202_simulada · `lead_id` CB-20261109-103942-SRLH · **`frase` ""** (envío sin datos personales: el chatbot no dice nada más) |

Payload: los mismos datos del evento, con `"name": ""`, `"email": ""`, `"company": ""`, `"phone": ""`, `"gdpr_consent": "no"` y `"marketing_consent": "no"`. En `conversation` no hay ningún dato personal, porque el cliente no llegó a darlo. Las tres últimas líneas:
```
Bot: Apuntado. Para que el equipo prepare tu propuesta y se ponga en contacto contigo, necesito tu nombre y tu email. ¿Aceptas…?
Client: No, prefiero no dar mis datos.
Bot: Sin problema, no guardamos tus datos. Gracias por tu consulta; si quieres que te respondamos, escríbenos a atencion@empresa-eventos.example.
```
Registro: `"id_conversacion": "conv-ruta-estrella-01a"`, `"enviado_n8n": "simulado"`, `"respuesta_n8n": "202_simulada"`, `"lead_id": "CB-20261109-103942-SRLH"`, `"consentimiento_datos": "no"`, `"consentimiento_publicidad": "no"`; el resto, igual que en la principal.

## Variante (b): escribe una tarjeta en el chat

Igual hasta B4. Después:

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C4b | Si hace falta, os paso ya mi tarjeta para reservar: 4111 1111 1111 1111. | Guardrails, regla 10 |
| B4b | No hace falta que me la des por aquí; no la guardo. Los pagos los gestiona el comercial con la propuesta. | Ejemplo de guardrails, tal cual |
| C5… | Sigue como la principal desde C5 (día, presupuesto y necesidades, "sí" a la privacidad y "no" a la publicidad) | `enviar_n8n.py` → simulado · 202_simulada · `lead_id` CB-20261109-103942-QVJZ · frase de éxito |

En el payload, la línea de la tarjeta sale tapada aunque hay consentimiento:
```
Client: Si hace falta, os paso ya mi tarjeta para reservar: [tarjeta].
```
Registro: `"id_conversacion": "conv-ruta-estrella-01b"`, `"consentimiento_datos": "si"`, sin ningún número de tarjeta.

## Reglas: ¿se cumplieron?

| # | Regla | ¿Cumple? |
|---|---|---|
| 1 | Aviso de IA en el primer mensaje, sin pedir datos | Sí |
| 2 | Router: `nuevo_evento`, ruta `lead`, `a_n8n` true, envio-n8n entre las skills | Sí |
| 3 | Disposición deducida del tipo y confirmada en la misma frase, recomendando en ese mismo mensaje | Sí |
| 4 | Máximo dos preguntas por mensaje entre todas las skills | Sí |
| 5 | Recomendación: espacios, orden y fotos del script; sin porcentajes ni precio; "por qué encaja" solo con `event_types` | Sí |
| 6 | La zona que da el cliente (Poblenou) se tiene en cuenta al recomendar | **No.** El recomendador no usa la zona: propone primero el Mirador (Montjuïc) y tercero el Fòrum (Les Corts). Solo el Llum está en Poblenou (fallo 1) |
| 7 | Espacio elegido → `preferred_location` con el nombre completo | Sí ("Llum" → "Llum del Poblenou") |
| 8 | Información dentro del evento (parking): con los datos del espacio, sin cambiar la ruta | Sí |
| 9 | Descuento: no se concede ni se insinúa, va al `message`, sin plazos | Sí |
| 10 | Día exacto después de elegir → se revalida el espacio | Sí (72 días; el Llum pide 7) |
| 11 | Cada dato se pregunta una sola vez | Sí |
| 12 | La pregunta de privacidad llega cuando ya están los datos de la consulta | **No.** Al contar como preguntado lo que el cliente no contestó, `listo_para_enviar` se vuelve true en C4 y la privacidad se pregunta antes del día, el presupuesto y las necesidades (fallo 2) |
| 13 | Consentimiento: datos y permiso en el mismo mensaje, con la política de privacidad; solo cuenta un "sí" claro | Sí. Pero hubo que repetir la pregunta, y la skill no dice si se puede (fallo 3) |
| 14 | Publicidad: una vez, después del "sí", aparte | Sí |
| 15 | Envío: una sola vez, solo con ruta `lead` y la privacidad respondida | Sí; la repetición no reenvía |
| 16 | Payload: 15 campos de texto; `event_date` solo con día exacto; `message` con necesidades y escalado | Sí |
| 17 | Sin URL ni clave: envío simulado (202_simulada) | Sí |
| 18 | Frase final de la skill envio-n8n §4, sin plazos ni promesas | Sí |
| 19 | Registro anónimo sin nombre, email, teléfono, empresa ni conversación | Sí |
| 20 | (a) "No" a la privacidad: envío sin datos personales, consentimientos `no`, frase vacía | Sí |
| 21 | (b) Tarjeta: no se guarda, se tapa en la conversación enviada | Sí |

**Resultado:** 19 de 21 reglas se cumplen. **Dos fallos (1 y 2)** y un punto que la skill no cubre (3). No he arreglado nada.

## Fallos y comentarios

1. **El recomendador no usa la zona.** El cliente pide Poblenou, pero `recomendar.py` solo mira aforo, antelación y horario. El primer espacio que propone es el Mirador (Montjuïc), y el Fòrum (Les Corts) sale tercero.
   - En el envío no afecta, porque el cliente eligió el Llum.
   - Si hubiera elegido el Mirador, n8n habría recibido un espacio fuera de la zona pedida.
2. **Privacidad demasiado pronto.** Con la regla "si no contesta, cuenta como preguntado" (cualificador §4), dos cambios de tema seguidos (parking y descuento) dejan la consulta "lista" sin día, presupuesto ni necesidades. El cliente los dio después por su cuenta; si no, la consulta habría salido sin ellos.
   - Opción: que solo cuente como preguntado cuando el cliente contesta algo a esa pregunta ("no lo sé"), no cuando cambia de tema.
3. **Repetir la pregunta de privacidad.** Consentimiento §4 dice que cambiar de tema no es un "sí", pero no dice si se vuelve a preguntar ni cuántas veces. Aquí se repitió una vez (B6).
4. **Empresa.** La presentación de producto es claramente corporativa, pero nadie pidió la empresa. Consentimiento §3 dice "Empresa: solo si el evento es corporativo", pero su frase fija solo pide nombre y email. `company` fue vacío.
5. **`resuelto_sin_humano`.** No está definido qué significa en una consulta que se envía al comercial. He puesto `no` porque lleva un escalado (descuento).
6. **El registro del plugin.** `enviar_n8n.py` escribe en `registros/` junto a los scripts. Dentro del plugin instalado, con el marketplace local, eso es `plugins/eventos-front-door/registros/` del repositorio. Está ignorado por `.gitignore`, pero es una carpeta del plugin, no del proyecto que lo usa.
