# KNOWLEDGE.md · Proyecto Front Door de eventos

Conocimiento acumulado del proyecto: enunciado, decisiones del grupo, cómo trabajar con Codex y lecciones de la prueba. Sirve a la vez de memoria para el equipo y de contexto para cualquier agente (Codex o Claude) que trabaje en el proyecto.

Última actualización: 8 de noviembre de 2026 · Clara Torrents

---

## 1. Contexto académico

- Máster en Science of AI in Business Administration (La Salle, URL). Asignatura: *Artificial Intelligence in Business: Concepts and Applications*.
- Encargo: rediseñar un proceso de negocio con IA, construir un **prototipo que funcione** y explicarlo en **una diapositiva para C-level** (qué cambia, por qué es útil y qué decisión pedimos a dirección).
- Siempre hay **revisión humana** al final del proceso.

### Evidencia que pide cada clase (lab sheet)
1. Contexto del equipo guardado.
2. Una skill útil, creada o encontrada.
3. Skill empaquetada como plugin.
4. Una tarea probada con una corrección anotada.
5. Una limitación conocida y lo que queda pendiente.

### Sesión 2: mejorar procesos y diapositivas
- Llevar la contraria a la IA: ¿lo usaríamos?, ¿qué falta?, ¿dónde añade trabajo?, ¿qué probaríamos primero?
- Explorar dos opciones, elegir una y guardar los motivos.
- Diapositiva: dar a la IA audiencia, mensaje, evidencia y estilo. Que suene al equipo y comprobar cada afirmación.

---

## 2. Decisión del grupo: opción A, "Customer front door"

Chatbot para una **empresa que alquila espacios para eventos**. Atiende a quien entra en la web, entiende qué quiere y lo resuelve o lo pasa a la persona adecuada.

- **Controla:** espacios, inventario (sillas, mesas, audiovisuales, catering), media (fotos, vídeos, planos, tours 360°), consentimiento y guardrails. Recoge cada consulta y la envía a n8n al final; la reserva la cierra el comercial (§3.2).
- **Nombre de la empresa:** pendiente (se usará `[EMPRESA]` hasta decidirlo).
- **Datos:** solo sintéticos (RGPD).

### Mapa del proceso

| Paso | Qué pasa | Quién |
|---|---|---|
| 1 | El visitante abre el chat | Usuario |
| 2 | Aviso de IA | Claude Code |
| 3 | El router clasifica la consulta | Claude Code |
| 3a | Información: responde con los datos del catálogo | Claude Code |
| 3b | Evento nuevo (con o sin espacio elegido): recomienda espacios con fotos y recoge los datos del evento | Claude Code |
| 3c | Queja, cambio de reserva, privacidad o persona sin consulta en marcha: da el contacto del equipo, sin prometer plazos. No va a n8n | Claude Code |
| 4 | Al final de la consulta: nombre, email y consentimiento; envío a n8n, una sola vez | Claude Code → n8n |
| 5 | Valida, completa datos con IA, asigna espacio y comercial, y puntúa | n8n |
| 6 | Email al cliente con enlace de Calendly, aviso al comercial y registro en Google Sheets | n8n |
| 7 | Llamada con el cliente y cierre de la reserva | Comercial |
| 8 | Dashboard de métricas | Claude Code |

Antes, el chat comprobaba disponibilidad y hacía prerreservas, y n8n abría tickets y reservaba hueco en el calendario (sustituido por §3.2).

**Reparto técnico:** Claude Code construye lo que ve el usuario (chat, dashboard). n8n recibe la consulta al final y hace el proceso por detrás (§3.2). El flujo de n8n lo construye Ale (documentos en `n8n/`). Antes: n8n llevaba calendario, reservas y tickets, y los flujos se iban a construir desde cero (sustituido por §3.2).

**Riesgos:** los chatbots están muy vistos, así que la diferencia debe venir del enrutado, la cualificación y la integración. Hay muchas rutas, así que la demo se centra en **tres**. Necesita una base de conocimiento para no inventar.

### Las skills (7 activas: la 5 y la 6 se descartan y se añade la 9, envio-n8n, §3.2)

| # | Skill | Bloque | Qué hace | Comprobación clave |
|---|---|---|---|---|
| 1 | router-intenciones | Atender | Clasifica: información, lead, cambio, incidencia (reserva se junta con lead, §3.2) | Si duda, pregunta |
| 2 | recomendador-espacios | Atender | 1 a 3 espacios según tipo de evento, asistentes y disposición (sin precio) | Solo catálogo; nunca aforo menor del pedido; regla del 90 % (ver §3.1) |
| 3 | media-espacios | Atender | Fotos, planos, tours 360° | Solo material con `approved: true`; si no hay (p. ej. vídeo), lo dice y ofrece lo que hay |
| 4 | cualificador-leads | Vender | Empresa, tipo, fecha, asistentes, presupuesto, urgencia; decide qué falta por preguntar | **Script** que devuelve los datos que faltan; ya no puntúa (la puntuación oficial es la de n8n, §3.2) |
| 5 | ~~disponibilidad-inventario~~ | — | **Descartada (sustituido por §3.2).** Antes: disponibilidad del espacio y extras | — |
| 6 | ~~gestor-reservas~~ | — | **Descartada (sustituido por §3.2).** Antes: prerreserva con bloqueo provisional de 72 h | — |
| 7 | consentimiento | Reglas | Aviso de IA, permiso antes de guardar, datos mínimos, publicidad aparte | El consentimiento viaja en el envío a n8n (`gdpr_consent`, `marketing_consent`). Antes: registro con fecha/hora real, finalidad e id_conversacion (sustituido por consentimiento v3 §6) |
| 8 | guardrails | Reglas | Tema, tono, escalado a persona | **Nunca da precios, presupuestos ni disponibilidad**; nunca descuentos; quejas y legal a persona |
| 9 | envio-n8n | Vender | Al final de una consulta, envía a n8n los 15 campos del contrato una sola vez y apunta cada conversación en el registro anónimo (§3.2) | **Script** `enviar_n8n.py`: tapa los datos que tocan, nunca reenvía y sin URL ni clave en el código |

**Orden:** 8 → 7 → 2 → 4. Las skills 5 y 6 se descartan (sustituido por §3.2).

Además existe la skill **buying-committee-simulator** (ya probada, con corrección registrada): simula el comité de compra del cliente y sirve para revisar propuestas de eventos corporativos grandes.

### Conversación de referencia
"Queremos una cena de empresa para 120 personas en marzo" → aviso de IA → nuevo lead → recomienda Llum del Poblenou (150 en banquete) con fotos y plano, y Mirador de Montjuïc como opción "al límite" (120) → recoge los datos del evento → nombre, email y consentimiento → envío a n8n → email con enlace de Calendly → llamada con el comercial. Si pide un 20 % de descuento: no se concede y va resumido en el `message` del envío para el comercial. Si pregunta el precio: lo prepara el comercial en una propuesta a medida.
Antes: n8n confirmaba la fecha y se hacía un bloqueo provisional de 72 h (sustituido por §3.2).

### Conceptos de la asignatura que hay que mostrar

| Concepto | Dónde aparece |
|---|---|
| Where AI gets it wrong | Guardrails, base de conocimiento, permisos limitados de n8n |
| LLMs vs. modelos de decisión | El router clasifica con el LLM sobre una lista cerrada de intenciones; lo que se hace con cada una y las demás decisiones van por script o tabla fija; el LLM redacta. En n8n, la IA propone la puntuación del lead y las reglas la limitan (§3.2) |
| AI workflows | Skills + n8n como herramientas + chatbot como agente |
| Aceleración vs. automatización | Consultas simples en automático; eventos grandes, quejas y excepciones con revisión humana |
| Capacity and total cost | Diapositiva: beneficios frente a integración, revisión, formación y mantenimiento |
| Human-in-the-loop | Paso 7 (llamada del comercial) y escalado desde guardrails |
| Lead journey | Diseñar primero la experiencia del organizador |
| Challenge the headline | Métricas concretas y límites explícitos en la diapositiva |

**Métricas candidatas:** tiempo de respuesta, % resuelto sin intervención humana, conversión consulta → reserva confirmada, satisfacción. (Antes la conversión pasaba por la prerreserva; sustituido por §3.2.)

---

## 3. Decisiones técnicas tomadas

| Decisión | Detalle | Motivo |
|---|---|---|
| Carpeta del proyecto | `/Users/claratorrents/Desktop/CODEX/Proyectos/front-door-eventos` | Fuera de OneDrive, que choca con git |
| Herramienta de construcción | **Claude Code** construye y ejecuta; Claude en el chat guía. El contenido lo escribe el equipo. | El profesor lo ha permitido |
| Escritura humana | Reglas de escritura en español en `AGENTS.md`. **humanizer-zh descartada** | Está pensada para chino |
| App → n8n | **Webhook de ida:** el chatbot envía la consulta al final y n8n solo responde si la ha recibido (contrato en §3.2) | Antes: webhook en ambos sentidos para disponibilidad y prerreserva (sustituido por §3.2) |
| Registro | n8n registra cada consulta enviada en **Google Sheets** (pestañas Enquiries, Processing log y Sentiment log). El chat guarda un registro anónimo de cada conversación en `registros/conversaciones.jsonl`, y el dashboard junta los dos (§3.2, decisión 11) | Antes: n8n añadía una fila por conversación (sustituido por §3.2) |
| Escritura directa de la app en Drive | **Descartada** | Exige credenciales de Google en la app, solo funciona de ida y la revisión periódica tiene límites |
| Puntuación de leads | La oficial es la de n8n: la IA propone y las reglas la limitan. El script del chat ya no puntúa (§3.2, decisiones 3 y 10) | Antes: script con pesos fijos, porque en la prueba el LLM dio 60, 20 y 40 con los mismos datos |
| Chat web del prototipo | Por reglas, sin API externa, en local. La única llamada fuera es el envío a n8n (§3.2) | Fiable, gratis y siempre igual para la demo |
| Compartir con el grupo | GitHub: `github.com/claratorrents/front-door-eventos` | Una sola versión para todos |

### 3.1 Decisiones de catálogo y negocio (5 de noviembre)
Datos en `data/espacios.json` (6 espacios) y `data/inventario.json` (10 extras). Validador: `scripts/validar_datos.py`. Revisión documentada en `pruebas/correccion-01-datos.md`.

**Precios**
- El chatbot **nunca da precios ni presupuestos** de nada: ni alquiler ni extras. Si el cliente pregunta: "El precio depende de la fecha, el montaje y los servicios. Te lo prepara el equipo comercial en una propuesta a medida."
- El chatbot **sí pregunta el presupuesto del cliente**, solo para cualificar. No lo compara en voz alta con nada.
- Los precios de los JSON son **uso interno** del comercial: orientativos, IVA no incluido.

**Inventario de extras**
- **Almacén compartido** entre los 6 espacios: el stock es para todos a la vez.
- El chatbot solo usa los nombres para reconocer lo que pide el cliente y lo **anota para el comercial** en el `message` del envío (§3.2). Nunca da precio ni confirma stock. Antes: el stock lo comprobaba n8n (sustituido por §3.2).
- `usable_in` limita en qué espacios tiene sentido cada extra.
- **Catering fuera del inventario**: el chatbot informa de la política del espacio (`catering_policy`) y lo anota en el `message` para el comercial (§3.2, decisión 6).

**Recomendador: regla del 90 %**
- Se usa el aforo de la **disposición pedida** (banquet, theater, cocktail, classroom), no el máximo absoluto.
- Si los asistentes superan el **90 %** de ese aforo, el espacio se marca **"al límite"**: se puede recomendar, pero después de las opciones cómodas y avisando al cliente.
- Ejemplo: cena para 120 en banquete → 1.º Llum del Poblenou (150, 80 %), Mirador de Montjuïc "al límite" (120, 100 %). La Nau (220, 55 %) se vería medio vacía.
- Por debajo del 60 % de ocupación no se recomienda, salvo que no haya otra opción. Ejemplo: para 120 en banquete la Nau (55 %) queda fuera.
- Si el cliente no indica disposición, se deduce del tipo de evento y se confirma en la misma frase ("Para una conferencia lo normal es formato teatro; ¿os encaja?"): conferencia o presentación → theater; cena o comida → banquet; networking o cóctel → cocktail; formación o taller → classroom.

**Prerreserva (bloqueo provisional): sustituido por §3.2.** No hay bloqueos: el siguiente paso es la llamada por Calendly. Antes: bloqueo gratuito de 72 h laborables solo para leads de más de 70 puntos, con día exacto, espacio elegido y antelación cumplida.
- Sigue valiendo: el chatbot nunca confirma una reserva (la cierra el comercial), y señal y cancelación quedan fuera del chatbot.
- La antelación mínima (`min_lead_time_days`) la sigue usando el recomendador para descartar espacios.

Pesos y niveles del cualificador: sustituido por §3.2 (decisión 10). El script del cualificador ya no puntúa: devuelve qué datos faltan por preguntar.

Ruta estrella de la demo: **consulta → recomendación con fotos → elige espacio → datos y consentimiento → envío → email con Calendly → llamada**. Antes: consulta → cualificación → recomendación → bloqueo provisional → propuesta del comercial (sustituido por §3.2).

**Reparto de leads**
- Cada espacio tiene `n8n_routing.sales_rep`: Marta Soler (Llum, Mirador), Oriol Puig (Jardí, Atelier), David Ramos (Fòrum, Nau).
- El comercial lo asigna **n8n**. Si el cliente eligió espacio, es el de ese espacio, porque el catálogo es el mismo (§3.2, decisiones 1, 2 y 9). Antes: el del primer espacio recomendado (sustituido por §3.2).
- Si no hay espacio que encaje, la consulta se envía igual y decide n8n. Una incidencia o un cambio de reserva no va a n8n: el chatbot da el contacto del equipo (§3.2, decisión 7). Antes: el lead iba a David Ramos y la incidencia abría un ticket (sustituido por §3.2).
- Se eliminó `default_lead_tier`: la prioridad sale de la puntuación de n8n (§3.2).

**Media**
- Cada archivo tiene ficha: `type` (foto, plano, tour360, video), `description` (qué muestra) y `approved`.
- Solo se enseña lo aprobado. Se elige la foto según el evento (cena → foto de banquete).
- A propósito para la demo: la foto 2 del Jardí de Gràcia (patio antes de la reforma) está **no aprobada**, y **no hay vídeos** (el chatbot debe decirlo y ofrecer el tour 360°).
- Al cliente nunca se le enseña la ruta del archivo: el chat web muestra imagen o enlace.

**Textos de cada espacio**
- `tagline`: frase corta de la tarjeta de recomendación.
- `full_profile`: solo si el cliente pide más detalles.
- `best_for`: lo usa el recomendador para encajar el tipo de evento.
- Se eliminaron `description` (repetía y decía "ficticia") y `max_capacity_alert` (igual que `absolute_max`).

**Decisiones y escalados (guardrails, 7 de noviembre)**

| decision | Cuándo | Quién lo recibe | Plazo |
|---|---|---|---|
| `ninguna` | Respuesta normal, sin escalar | — | — |
| ~~`consulta_disponibilidad`~~ | **Sustituido por §3.2:** no se comprueba disponibilidad. Si preguntan: "lo confirma el comercial cuando te contacte" | — | — |
| `pendiente_confirmar` | Pregunta sin dato en el catálogo (accesibilidad, horario interior…) | Dentro de una consulta: va al `message` del envío. Fuera: el chatbot da el contacto del equipo | Dentro: "Lo confirmará el comercial cuando te contacte." Fuera: sin plazos. Antes: equipo de atención en 24 h laborables (sustituido por §3.2) |
| ~~`prerreserva`~~ | **Sustituido por §3.2:** no hay bloqueos | — | — |
| `escalar_comercial` | Descuentos, catering, extras, excepciones, permisos | Dentro de una consulta: va resumido en el `message` del envío y el comercial lo ve en su resumen de n8n (§3.2, decisión 6). Antes: comercial del espacio o David Ramos | Sin plazo en horas: "Lo verás con el comercial cuando te contacte." Antes: 24 h laborables (sustituido por §3.2) |
| `escalar_humano` | Quejas, legal, cambios de reserva, mensajes ofensivos repetidos | Fuera de una consulta: el chatbot da el contacto del equipo; no va a n8n (§3.2, decisión 7) | **Sin plazos** (decisión 7). Antes: 24 h laborables |
| `escalar_humano` | Pide persona o frustración | Sin consulta en marcha: el chatbot da el contacto del equipo (§3.2, decisión 7). Con una consulta en marcha (persona o frustración): se ofrece cerrar y enviar la consulta ya, y además se da el contacto del equipo | Sin plazos. Antes: en horario, menos de 2 h; fuera de horario, el siguiente día laborable (a primera hora si quedaban menos de 2 h para el cierre) |

- **Horario de atención (lunes a sábado, de 9 a 18 h):** se mantiene solo como dato junto al contacto del equipo. "24 h laborables" queda sustituido por §3.2: el chatbot no promete plazos en horas. Antes: como máximo, el siguiente día laborable a la misma hora.
- Ofensivo: primer mensaje, aviso y sigue (`ninguna`); si repite, cierra y `escalar_humano`.
- Contacto del equipo de atención: atencion@empresa-eventos.example · +34 930 000 000 (lunes a sábado, de 9 a 18 h)
- Frustración: el cliente dice que no le entendemos o repite la misma petición dos veces.
- Disponibilidad: nunca se comprueba. Si preguntan: "lo confirma el comercial cuando te contacte" (§3.2, decisión 4). Antes: "Según el calendario, ese día parece libre…" con dato de n8n (sustituido por §3.2).

- "Lo compruebo" y "lo confirmo" siempre llevan su `decision` y dicen quién responde, sin plazos en horas. Dentro de una consulta: "Lo verás con el comercial cuando te contacte."; fuera, el contacto del equipo (§3.2, decisión 7).
- Para enviar la consulta, el **email es obligatorio**; el teléfono es opcional (§3.2, decisión 5). Se pide con consentimiento. Si el cliente no da email, se le dan los datos del equipo: atencion@empresa-eventos.example · +34 930 000 000. Antes: se ofrecía una vez la alternativa entre teléfono y email (sustituido por §3.2). Y se aprovecha para seguir cualificando.
- Las frases fijas se traducen al catalán o al inglés manteniendo el sentido exacto, sin añadir promesas.
- Pruebas: `pruebas/prueba-guardrails-01.md`, `pruebas/prueba-guardrails-02.md` y `pruebas/prueba-guardrails-03.md`. Corrección: `pruebas/correccion-02-guardrails.md`.

**Pendiente:**
- Nombre de la empresa (cambiar también el campo `project`).
- ~~Chat web: tapar tarjetas, IBAN y DNI siempre, y email y teléfono si no hay permiso, antes de guardar la conversación o enviarla a n8n.~~ Hecho: lo hace `scripts/enviar_n8n.py` (9 de noviembre).
- ~~Chat web: usar la hora real para saber si se está en horario de atención.~~ Sustituido: el horario solo se da como dato junto al contacto del equipo y no se prometen plazos (§3.1).
- n8n: si el cliente retira el permiso, borrar también sus datos del Sheet.
- Media: las 12 fotos están en media/placeholders/ (ilustrativas, generadas con IA). Los 6 planos son SVG esquemáticos generados con los datos (`scripts/generar_planos.py`, "Plano orientativo"). Los tours 360° están con `approved: false` hasta que exista uno de verdad; en el chat, "más fotos" es una galería.

### 3.2 Integración con el flujo de n8n de Ale (8 de noviembre)
Documentos de Ale en `n8n/`: contrato del webhook, explicación del flujo, JSON del flujo (v1) y diagrama. La guía de Amit lleva credenciales y está en `.gitignore`: nunca se sube.

**Qué hace cada parte**
| Parte | Hace | No hace |
|---|---|---|
| Chatbot (Claude Code) | Atiende, recomienda espacios con fotos, recoge los datos, pide consentimiento y, al final, envía la consulta a n8n | Puntuación oficial, bloqueos, disponibilidad, emails |
| n8n (Ale) | Guarda, valida, completa datos con IA, asigna espacio y comercial, puntúa, envía al cliente un email con enlace de Calendly, avisa al comercial y lo registra todo en Google Sheets (pestañas Enquiries, Processing log y Sentiment log) | — |
| Comercial | Llamada con el cliente (Calendly) y cierre de la reserva | — |

**Las 5 decisiones del equipo**
1. **Un solo catálogo:** los 6 espacios de `data/espacios.json`. Ale los copia a su hoja "IE007 – Database" (pestañas Spaces y Reps).
2. **El chat recomienda y enseña los espacios con fotos.** Si el cliente elige uno, su nombre va en `preferred_location`, para que n8n asigne ese mismo espacio.
3. **La puntuación oficial es la de n8n** (es la que decide el email al cliente). El cualificador del chat solo decide qué preguntar; su puntuación no se envía ni decide nada.
4. **Fuera el bloqueo de 72 h y las skills 5 y 6.** El siguiente paso lo marca n8n: un email con enlace de Calendly cuando la consulta encaja, o el contacto de una persona del equipo cuando no. El chatbot nunca comprueba disponibilidad: si preguntan, "lo confirma el comercial cuando te contacte".
5. **Email obligatorio** para enviar la consulta. Quejas, cambios de reserva, privacidad y fuera de tema **no van a n8n**: el chatbot da el contacto del equipo (skills guardrails y consentimiento).

**Más decisiones (8 de noviembre)**
6. **Escalados dentro de una consulta** (descuento, catering, extras a medida, excepciones, permisos): no se escalan aparte. Se resumen en el campo `message` del envío y el comercial los ve en su resumen de n8n.
7. **Escalados fuera de una consulta** (queja, cambio de reserva, privacidad, petición de hablar con una persona sin consulta en marcha): el chatbot da el contacto del equipo (atencion@empresa-eventos.example · +34 930 000 000) y **no promete plazos**, porque ningún canal lleva el caso.
8. **La intención `reserva` se junta con `nuevo_evento`:** no hay bloqueos, y el espacio elegido viaja en `preferred_location`.
9. **Nombre del comercial:** solo se dice si el cliente ha elegido un espacio (n8n le asignará el comercial de ese espacio, porque el catálogo es el mismo). Si no: "el comercial que lleve tu evento".
10. **Cualificador:** su script ya no puntúa; devuelve qué datos faltan por preguntar.
11. **Registro de cada conversación:** el chat guarda un registro anónimo de cada conversación en `registros/conversaciones.jsonl` (intención, ruta, resuelto sí/no, enviado a n8n sí/no, consentimiento sí/no). El dashboard junta ese registro con las hojas de Ale. Campos: ver [Registro anónimo de conversaciones](#registro-anónimo-de-conversaciones).

**Cuándo se envía**
- Una sola vez por consulta, al final de una ruta `lead`, cuando el cliente ha dado nombre y email y ha respondido a la pregunta de privacidad.
- Si se envía dos veces, el cliente recibe dos emails: nunca se reenvía, salvo un único reintento si no hubo respuesta (mismo `lead_id`).

**Contrato del webhook (sustituye al contrato anterior)**
POST a `N8N_WEBHOOK_URL` con las cabeceras `Content-Type: application/json` y `X-API-Key: N8N_API_KEY`. Los 15 campos van siempre, como texto; si no se conoce un dato, `""`.

| Campo | Qué envía el chatbot |
|---|---|
| `lead_id` | `CB-` + AAAAMMDD-HHMMSS + 4 caracteres aleatorios. Único, nunca se reutiliza |
| `timestamp` | Fecha y hora real, ISO 8601 en UTC |
| `name` | Nombre y apellidos (obligatorio) |
| `email` | Email del cliente (obligatorio) |
| `company` | Empresa, si es corporativo |
| `phone` | Teléfono con prefijo, si lo da |
| `preferred_location` | El espacio elegido (p. ej. "Llum del Poblenou"); si no eligió, la zona que dijo; si no, `""` |
| `event_type` | Tipo de evento, en palabras del cliente |
| `event_date` | AAAA-MM-DD solo si hay día exacto; si solo dijo el mes, `""` (n8n lo lee de la conversación) |
| `guests` | Asistentes, como los dijo (número o rango) |
| `budget_eur` | Presupuesto, como lo dijo (número o rango) |
| `message` | Lo que pide, en sus palabras (extras, necesidades) |
| `conversation` | Transcripción completa, una línea por turno empezando por `Bot:` o `Client:`, separadas por `\n`, con tarjetas, IBAN y DNI tapados |
| `gdpr_consent` | `yes` / `no` |
| `marketing_consent` | `yes` / `no` |

**Respuestas de n8n**
| Respuesta | Qué hace el chatbot |
|---|---|
| 202 | "Gracias. El equipo se pondrá en contacto contigo en breve." (en el idioma del cliente) |
| 403 / 404 | No reintenta. "No he podido enviar tu consulta. Escríbenos a atencion@empresa-eventos.example o llámanos al +34 930 000 000 (de lunes a sábado, de 9 a 18 h) y te atendemos." Se registra el error en el log del servidor |
| Sin respuesta en 10 s | Un único reintento con el mismo `lead_id` |

**Reglas que no se saltan**
- La URL y la clave solo en variables de entorno (`N8N_WEBHOOK_URL`, `N8N_API_KEY`), en el servidor. Nunca en el navegador, el código, el repositorio ni el chat.
- Mientras Amit no pase la URL y la clave, el envío se **simula** (respuesta 202 SIMULADA) con el mismo formato.
- En pruebas reales, solo emails de prueba de Ale (`alejandro+ie007-xxx@alelabs.es`), nunca datos reales.
- **Por confirmar con Ale:** si el cliente dice "no" a la privacidad, proponemos enviar la consulta **sin** nombre, email, teléfono ni empresa (con `gdpr_consent: no`), para que quede contada sin guardar datos personales.

#### Registro anónimo de conversaciones
Una línea por conversación en `registros/conversaciones.jsonl`, vaya o no a n8n (decisión 11). Lo escribe `scripts/enviar_n8n.py` (skill `envio-n8n`) en la carpeta desde la que se ejecuta el chat (directorio de trabajo), nunca dentro de la carpeta del plugin.

| Campo | Valores |
|---|---|
| `id_conversacion` | conv-… |
| `fecha_hora` | UTC, ISO 8601 |
| `idioma` | es / ca / en |
| `ruta` | informacion / lead / cambio / incidencia / privacidad / fuera_tema |
| `rutas_adicionales` | lista |
| `decision` | ninguna / pendiente_confirmar / escalar_comercial / escalar_humano |
| `motivo_escalado` | el de guardrails, o — |
| `espacio_elegido` | nombre del catálogo o "" (no es dato personal) |
| `enviado_n8n` | si / no / simulado |
| `respuesta_n8n` | 202 / 202_simulada / 403 / 404 / sin_respuesta / — |
| `lead_id` | el enviado, o "" (une con la hoja Enquiries de Ale) |
| `consentimiento_datos` | si / no |
| `consentimiento_publicidad` | si / no |
| `resuelto_sin_humano` | si / no. Lo calcula el script: `no` si la decision es `escalar_humano` o `pendiente_confirmar`, o si el chatbot dio el contacto del equipo fuera de una consulta; `si` en el resto, incluidas las consultas enviadas a n8n aunque lleven escalados en el message (es el proceso normal) |

Nunca: nombre, email, teléfono, empresa, texto de la conversación.

### Riesgos de la integración con n8n
1. **n8n Cloud o local:** en Cloud, conectar Google es iniciar sesión. En local, Google exige credenciales en Google Cloud Console.
2. **Cuenta de Google:** la de la universidad puede bloquear apps externas. Alternativa: una Gmail del proyecto.
3. **Campos que cambian:** se evita con el contrato de la §3.2.
4. **Mitigación:** prueba mínima de punta a punta en cuanto haya n8n (una conversación → webhook → una fila en el Sheet).

---

## 4. Cómo funciona Claude Code

La prueba inicial se hizo con Codex (proyecto reservas-eventos); el profesor permitió pasar a Claude Code.

### Las 4 capas
| Capa | Qué es |
|---|---|
| Prompt | Lo que se pide en cada momento |
| `CLAUDE.md` | Contexto permanente; Claude Code lo carga al empezar cada sesión. Aquí solo contiene `@AGENTS.md`, que importa ese archivo |
| Skills | `.claude/skills/<nombre>/SKILL.md`; Claude Code solo ve nombre y descripción y carga el resto cuando la necesita |
| Plugin | Paquete instalable con skills (y otros componentes); sirve para compartir |

### Skills
- **Del proyecto:** `.claude/skills/<nombre>/SKILL.md`. Van en el repo y las usa cualquiera que abra el proyecto.
- **Personales:** `~/.claude/skills/<nombre>/SKILL.md`. Solo en tu ordenador, para todos tus proyectos.
- La carpeta de la skill puede llevar más archivos (scripts, ejemplos, plantillas) junto a `SKILL.md`; la skill los cita y Claude los abre cuando hacen falta.
- Se activa sola cuando la descripción encaja con la tarea, o a mano escribiendo `/<nombre>`.

### Formato de una skill
```markdown
---
name: nombre-de-la-skill
description: Cuándo SÍ se usa y cuándo NO. Es lo que decide si se activa.
---
Instrucciones como comprobaciones concretas.
Ejemplos de respuesta buena y mala.
```
Es el mismo formato `SKILL.md` que en Codex: las skills de la prueba se pueden reutilizar copiando su carpeta a `.claude/skills/`.

### Plugin
```
plugins/eventos-front-door/
├── .claude-plugin/plugin.json   ← solo este archivo dentro de .claude-plugin
└── skills/<nombre>/SKILL.md
```
- `plugin.json` lleva al menos `name`; también puede llevar `description`, `version` y `author`.
- Además de `skills/`, un plugin puede llevar `commands/`, `agents/`, `hooks/` y servidores MCP. Para este proyecto basta con `skills/`.
- Las skills de un plugin instalado se llaman con el nombre del plugin delante: `eventos-front-door:<skill>`.
- Probar sin instalar: `claude --plugin-dir ./plugins/eventos-front-door`.
- Las skills ya funcionan dentro del proyecto desde `.claude/skills/` sin instalar el plugin; el plugin sirve para compartir.

### Marketplace (equivalente a `.agents/plugins/marketplace.json`)
- Archivo en la raíz del repo: `.claude-plugin/marketplace.json`, con `name`, `owner` y la lista `plugins` (cada uno con `name` y `source`, por ejemplo `"./plugins/eventos-front-door"`).
- Añadir el marketplace: `/plugin marketplace add ./` (carpeta local) o `/plugin marketplace add usuario/repo` (GitHub).
- Instalar: `/plugin install eventos-front-door@<nombre-del-marketplace>`, o desde el menú de `/plugin`.

### Comprobado al instalar el plugin (7 de noviembre, Claude Code 2.1.317)
- **El plugin se genera, no se edita:** `python3 scripts/empaquetar_plugin.py` crea `plugins/eventos-front-door/` (desde la versión 0.2.0, del 9 de noviembre: 7 skills, 5 scripts sin tests, `data/`, `media/`, `KNOWLEDGE.md`, `AGENTS.md`, README) y `.claude-plugin/marketplace.json`.
- **Validación:** `claude plugin validate plugins/eventos-front-door` y `claude plugin validate .` pasan. Solo avisa de que falta una licencia, que únicamente exige el directorio público de plugins.
- **Instalación desde el terminal (funciona):** `claude plugin marketplace add <ruta-del-repo>` y después `claude plugin install eventos-front-door@front-door-eventos --scope user`. No pide iniciar sesión. `claude plugin list` lo muestra activado y `claude plugin details eventos-front-door` lista las 6 skills (unos 670 tokens fijos por sesión).
- **Marketplace local:** con un marketplace de carpeta local, Claude Code lee el plugin directamente de `plugins/eventos-front-door` del repositorio, sin copiarlo aparte.
- **Cuándo cargan las skills:** en el mismo mensaje en que se instala, la skill todavía no existe ("Unknown skill"). Desde el mensaje siguiente ya aparece también en la sesión que estaba abierta (`eventos-front-door:recomendador-espacios` cargó con sus rutas sustituidas). No hace falta reiniciar la app ni abrir una sesión nueva, aunque en una sesión nueva también funciona.
- **Rutas:** al cargar una skill, Claude Code sustituye `${CLAUDE_SKILL_DIR}` por la carpeta de la skill (visto en el código de la CLI). Aplicando esa sustitución sobre el plugin instalado, las rutas a scripts, datos y `KNOWLEDGE.md` de las 6 skills existen. `recomendar.py` y `validar_datos.py` funcionan ejecutados desde otra carpeta.
- **Desinstalar:** `claude plugin uninstall eventos-front-door@front-door-eventos` y `claude plugin marketplace remove front-door-eventos`.
- **Prueba en una sesión nueva, fuera del proyecto** (carpeta `prueba-plugin`, app de escritorio):
  - La skill `eventos-front-door:recomendador-espacios` carga por su nombre.
  - Las rutas a `recomendar.py` y a `data/` resuelven dentro del plugin instalado (con el marketplace local, `plugins/eventos-front-door/` del repo). Con 120 personas en banquete sale Llum del Poblenou `comodo` (foto-01) y Mirador de Montjuïc `al_limite` (foto-02), sin porcentajes para el cliente.
- **`/plugin` en la app de escritorio:** no comprobado. La instalación por terminal (`claude plugin marketplace add` / `claude plugin install`) sí funciona, así que es la vía que se usa.

### Codex vs. Claude Code (mismos conceptos, otros nombres)
| | Codex | Claude Code |
|---|---|---|
| Contexto | `AGENTS.md` | `CLAUDE.md` (aquí importa `AGENTS.md`) |
| Skills | `.agents/skills/` | `.claude/skills/` |
| Formato de skill | `SKILL.md` (estándar abierto) | `SKILL.md` (mismo estándar) |
| Manifiesto del plugin | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` |
| Marketplace | `.agents/plugins/marketplace.json` | `.claude-plugin/marketplace.json` |
| Instalar | `/plugins` | `/plugin` |

---

## 5. Lecciones de la prueba (proyecto `reservas-eventos`)

1. **Las carpetas que empiezan por punto están ocultas** en el Mac (`.agents`, `.git`). Se ven con `Cmd + Mayús + .` o pidiendo a Codex que las liste.
2. **OneDrive y git chocan.** Proyecto fuera de carpetas sincronizadas.
3. **`.DS_Store`** lo crea el Mac: va en `.gitignore`.
4. **Sin `npx`**, una skill se instala clonando el repositorio con git y copiando la carpeta que contiene `SKILL.md`.
5. **humanizer-zh** (skill del profesor) está pensada para chino. Las reglas de escritura humana en español van en `AGENTS.md`.
6. **Chat de trabajo** para construir; **chat nuevo** para probar como cliente.
7. **Leer cada respuesta como cliente:** la primera respuesta al descuento era correcta pero seca; mejoró al dar un plazo (24 h laborables) y aprovechar para cualificar.
8. **Probar también el camino del "no"** (cliente que no da datos, que pide descuento, que se queja).
9. **El LLM no puntúa de forma estable.** Con los mismos datos dio 60, luego 20 (asistentes 20 → 0), y luego 40 con script. Las decisiones van con reglas fijas.
10. **Un dato "pendiente de aclarar" no puede llevar la puntuación máxima.**
11. **Hacer 5 preguntas en un mensaje es demasiado:** una o dos cada vez.
12. **Nada de rutas de archivo al cliente:** la media se muestra como imágenes y enlaces.
13. **AGENTS.md funciona:** Codex pidió aprobación del plan antes de crear el chat web, tal como estaba escrito (human-in-the-loop).
14. **Nunca pegar claves de API en el chat.**

Pesos de la prueba para el cualificador, como punto de partida: fecha 25 · asistentes 20 · presupuesto 20 · tipo de evento 15 · empresa 10 · urgencia 10. Más de 70 → prerreserva; 70 o menos → comercial. **Decididos el 7 de noviembre (mismos pesos): niveles y condiciones en la skill cualificador-leads.**

---

## 6. Reglas de oro para trabajar con el agente

- Una tarea por prompt.
- Prompt = objetivo + contexto + restricciones + cómo comprobarlo.
- Pedir plan antes de cambios grandes.
- Exigir que ejecute la comprobación: un "hecho" no es una prueba.
- "Haz commit" tras cada paso que funcione.
- Llevar la contraria a la IA y documentar cada corrección (antes / problema / cambio / después) en `pruebas/correccion-XX-<skill>.md`.
- Decidir con reglas, redactar con el LLM.
- Solo datos inventados.

**Frases de prueba:** "Queremos una cena de empresa para 120 personas en marzo" · "¿Me hacéis un 20 % si reservo hoy?" · "Prefiero no dar mi email" · "Quiero poner una reclamación".

---

## 7. Estado actual y próximos pasos

### Hecho
- [x] Prueba completa en `reservas-eventos` (contexto, 5 skills, correcciones, plugin, chat web).
- [x] Guía `Guia_rapida_Codex.docx`.
- [x] Paso 1: carpeta `front-door-eventos` creada y abierta en Claude Code.
- [x] Paso 2: `AGENTS.md` (commit `4b17310`; regla 2 actualizada a "nunca dar precios" en `7a5ebe4`) y `CLAUDE.md` (`5f00b31`).
- [x] Paso 3: catálogo, inventario y validador (commits `7a5ebe4` y `121a83b`), con corrección 01 documentada.
- [x] Paso 4: skills de guardrails (`e323834`, `6a11b2c`, `1d8b780`) y consentimiento (`bea7691`), con pruebas y correcciones 02 y 03.
- [x] Paso 5 (en parte): recomendador-espacios con `scripts/recomendar.py` (`591885a` a `5596168`), cualificador-leads con `scripts/puntuar_lead.py` (`7968a5d`, `2e175ae`; sustituido por `scripts/datos_consulta.py`, §3.2) y media-espacios (`434d83a`, `7387f50`), con pruebas y correcciones 04, 05 y 06.
- [x] Resumen del trabajo: `RESUMEN.md` (`b368618`) y `SUMMARY.md` en inglés (`6bba9a5`).
- [x] Paso 5: router-intenciones con `scripts/router.py` y validación del espacio elegido en `scripts/recomendar.py`, con pruebas 01-02 y corrección 07.
- [x] Paso 7: plugin `eventos-front-door` (`9bdb81c`), instalado y probado en una sesión nueva (`1d6dddf`). Ver §4.
- [x] Fotos: las 12 en `media/placeholders/`, ilustrativas y generadas con IA (`0b0451b`). El validador comprueba que cada foto aprobada tiene su archivo, y el plugin incluye `media/`.
- [x] Planos en SVG: las urls de `data/espacios.json` apuntan a `plano.svg` (`a68026c`). Los archivos todavía no existen.
- [x] Paso 13: repositorio en GitHub, `github.com/claratorrents/front-door-eventos`.
- [x] Integración con n8n: decisiones y contrato del webhook de Ale en §3.2 (`f33b7bb`).
- Tests al 9/11: `chat/test_entender.py` 127/127, `chat/test_rutas.py` 2163/2163, `chat/frases_dificiles.py` 17/17 seguras, `test_recomendar.py` 35/35, `test_generar_planos.py` 14/14, `test_datos_consulta.py` 13/13, `test_router.py` 12/12, `test_enviar_n8n.py` 17/17; validador correcto (avisa de los planos y tours que faltan).

### Pendiente inmediato
- [ ] Decidir el nombre de la empresa.
- [ ] Paso 2 de la integración con n8n (adaptar el proyecto a la §3.2), en 8 puntos: 1. `AGENTS.md` y `KNOWLEDGE.md` · 2. consentimiento · 3. cualificador · 4. router · 5. guardrails · 6. recomendador · 7. skill nueva de envío a n8n · 8. regenerar el plugin y prueba completa.
  - Hecho: 1 (`747b8ab`, `af71d87`); 2, consentimiento versión 3 (`f80294f`, `0405c3e`); 3, cualificador con `scripts/datos_consulta.py`, que ya no puntúa (`8d1ce27`, corrección 09); 4, router sin la intención `reserva`, con `a_n8n` y `--consulta-en-marcha` (`ee2c71f`, `bf737b3`, corrección 10); 5, guardrails (`52b9313`, `b815673`, corrección 11); 6, recomendador (`e641c20`, `0c5cd9a`, `f61f1f4`, corrección 12); 7, skill `envio-n8n` con `scripts/enviar_n8n.py` y el registro anónimo (`b689180`, `c2dc7f9`); 8, plugin 0.2.0 regenerado y prueba completa de la ruta estrella con envío simulado (`pruebas/prueba-envio-n8n-01.md`: 19 de 21 reglas; dos fallos: el recomendador no usaba la zona y la privacidad llegaba antes de tener los datos). Arreglados en el plugin 0.2.1: zona en `recomendar.py`, preguntas pendientes en `datos_consulta.py`, frase de privacidad con la empresa, `resuelto_sin_humano` calculado y registro en el directorio de trabajo (`pruebas/prueba-envio-n8n-02.md`: 21 de 21 reglas). Plugin 0.2.2: `--validar` con `--zona` y los textos de zona (`bajo_60`) y de preguntas del cualificador.
  - **Punto 7 (skill `envio-n8n`), decidido el 8 de noviembre** (hecho: lo aplican la skill y `scripts/enviar_n8n.py`) (sale de la prueba 03 de consentimiento):
    - Sin "sí" a la privacidad: `marketing_consent: no`.
    - Si el cliente no contesta a la publicidad o cierra el chat: se envía con `marketing_consent: no`.
    - Tras un "no" a la privacidad, un solo mensaje: "Sin problema, no guardamos tus datos. Gracias por tu consulta; si quieres que te respondamos, escríbenos a atencion@empresa-eventos.example." (consentimiento §4).
    - Sin consentimiento, en `conversation` se tapan nombre, email, teléfono y empresa.
    - Solo teléfono (acepta pero no da email): se envía sin datos personales, como un "no", y se le da el teléfono del equipo.
    - Campos del registro anónimo (`registros/conversaciones.jsonl`, decisión 11): fijados en la tabla de la §3.2.
- [x] Paso 8: chat web en `chat/` (9 de noviembre). Por reglas, sin API externa ni instalar nada: servidor con la biblioteca estándar de Python y una página HTML, CSS y JavaScript.
  - **Arrancar:** desde la carpeta del proyecto, `python3 chat/servidor.py` y abrir en el navegador la dirección `127.0.0.1:8000`. El envío a n8n es SIMULADO mientras no haya `N8N_WEBHOOK_URL` y `N8N_API_KEY`; el registro anónimo va a `registros/` (ignorado por git). `.claude/launch.json` lo tiene configurado, pero la app de escritorio no puede leer el Escritorio (permiso de macOS), así que se arranca desde el terminal.
  - **Piezas:** `entender_reglas.py` (lee el mensaje: intención y datos, por palabras clave es/en; se puede cambiar por un LLM con la misma entrada y salida), `conversacion.py` (estado y orden de los pasos; decide con `router.py`, `recomendar.py`, `datos_consulta.py` y `enviar_n8n.py`), `frases.json` (todas las frases es/en), `config.py` ([EMPRESA] y contacto en un solo sitio).
  - **Tests:** `chat/test_entender.py` (18 pasos × 6 formas de decirlo y casos sueltos) y `chat/test_rutas.py` (las 3 rutas de la demo con el guion fijo, cada paso con sus 5 variantes, casos de error y el servidor). Variantes de prueba en `chat/variantes.py` y traducciones al inglés, aprobadas por el equipo el 9/11.
  - **Frases difíciles** (`python3 chat/frases_dificiles.py`): 17 frases coloquiales, con faltas o con datos mezclados. Se exige que todas las respuestas sean seguras (sin precio, promesa ni dato inventado, y nunca callado), no que se entiendan todas: hoy, 17/17 seguras y 14/17 con algo entendido.
  - **Ajustes del 9/11, tras la revisión:** "classroom" se dice "taller" / "workshop"; planos en el idioma de la conversación (`plano.svg` y `plano.en.svg`); frase nueva para un espacio elegido que no cabe por aforo; B14 con botones "Sí, envíalo" / "No, sigamos" y el contacto del equipo; ante una inyección que pide confirmar la reserva, B4 (y la 23 sin su pregunta solo si pide el prompt).

### Plan
1. Carpeta y proyecto en Claude Code.
2. `AGENTS.md` + estructura + `.gitignore`.
3. Catálogo de espacios e inventario sintéticos (con validador).
4. Skills 8 y 7 (guardrails, consentimiento).
5. Skills 1, 2, 3 y 4 (router, recomendador, media, cualificador con script).
6. Pruebas y correcciones documentadas.
7. Plugin `eventos-front-door` de Claude Code: `plugins/eventos-front-door/` con `.claude-plugin/plugin.json` y las skills, más `.claude-plugin/marketplace.json` en la raíz para instalarlo desde el repo (ver §4).
8. (Hecho) Chat web + envío de la consulta a n8n con el contrato de la §3.2 (simulado hasta tener la URL y la clave). Antes: resumen estructurado por conversación en local (sustituido por §3.2).
9. n8n: prueba de punta a punta con el flujo de Ale (una consulta → respuesta 202 → fila en Enquiries), solo con emails de prueba de Ale. Las skills 5 y 6 se descartan (§3.2).
10. Dashboard de métricas.
11. Elegir las 3 rutas de la demo.
12. Diapositiva ejecutiva.
13. GitHub para el grupo (hecho).
