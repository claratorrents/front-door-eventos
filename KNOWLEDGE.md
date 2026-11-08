# KNOWLEDGE.md · Proyecto Front Door de eventos

Conocimiento acumulado del proyecto: enunciado, decisiones del grupo, cómo trabajar con Codex y lecciones de la prueba. Sirve a la vez de memoria para el equipo y de contexto para cualquier agente (Codex o Claude) que trabaje en el proyecto.

Última actualización: 7 de noviembre de 2026 · Clara Torrents

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

- **Controla:** espacios, inventario (sillas, mesas, audiovisuales, catering), media (fotos, vídeos, planos, tours 360°), consentimiento y guardrails. Gestiona leads y reservas.
- **Nombre de la empresa:** pendiente (se usará `[EMPRESA]` hasta decidirlo).
- **Datos:** solo sintéticos (RGPD).

### Mapa del proceso

| Paso | Qué pasa | Quién |
|---|---|---|
| 1 | El visitante abre el chat | Usuario |
| 2 | Aviso de IA y consentimiento antes de guardar datos | Claude Code |
| 3 | El router clasifica la consulta | Claude Code |
| 3a | Información: responde desde la base de conocimiento | Claude Code |
| 3b | Lead o reserva: cualifica, recomienda, comprueba disponibilidad, prerreserva | Claude Code + n8n |
| 3c | Incidencia o cambio: abre ticket | n8n |
| 4 | Valida, enriquece y puntúa el lead | n8n |
| 5 | Reserva hueco en calendario y avisa al equipo | n8n |
| 6 | Reunión comercial o seguimiento | Persona |
| 7 | Sentimiento y registro de cada conversación | n8n |
| 8 | Dashboard de métricas | Claude Code |

**Reparto técnico:** Claude Code construye lo que ve el usuario (chat, dashboard). n8n ejecuta el proceso por detrás (calendario, reservas, avisos, tickets, registro). Los flujos de n8n se construyen desde cero.

**Riesgos:** los chatbots están muy vistos, así que la diferencia debe venir del enrutado, la cualificación y la integración. Hay muchas rutas, así que la demo se centra en **tres**. Necesita una base de conocimiento para no inventar.

### Las 8 skills

| # | Skill | Bloque | Qué hace | Comprobación clave |
|---|---|---|---|---|
| 1 | router-intenciones | Atender | Clasifica: información, lead, reserva, cambio, incidencia | Si duda, pregunta |
| 2 | recomendador-espacios | Atender | 1 a 3 espacios según tipo de evento, asistentes y disposición (sin precio) | Solo catálogo; nunca aforo menor del pedido; regla del 90 % (ver §3.1) |
| 3 | media-espacios | Atender | Fotos, planos, tours 360° | Solo material con `approved: true`; si no hay (p. ej. vídeo), lo dice y ofrece lo que hay |
| 4 | cualificador-leads | Vender | Empresa, tipo, fecha, asistentes, presupuesto, urgencia; puntúa | Puntuación con **script** de pesos fijos |
| 5 | disponibilidad-inventario | Vender | Disponibilidad del espacio para la fecha; anota los extras que pide el cliente | Nunca confirma sin dato real de n8n; extras sin precio ni promesa de stock |
| 6 | gestor-reservas | Vender | Prerreserva = bloqueo provisional gratuito de 72 h (ver §3.1) | Confirmación expresa del cliente; nunca confirma la reserva final |
| 7 | consentimiento | Reglas | Aviso de IA, permiso antes de guardar, datos mínimos, publicidad aparte | Registro con fecha/hora real, finalidad e id_conversacion |
| 8 | guardrails | Reglas | Tema, tono, escalado a persona | **Nunca da precios ni presupuestos**; nunca confirma disponibilidad sin n8n; nunca descuentos; quejas y legal a persona |

**Orden:** 8 → 7 → 2 → 4. Las skills 5 y 6 dependen de tener n8n conectado.

Además existe la skill **buying-committee-simulator** (ya probada, con corrección registrada): simula el comité de compra del cliente y sirve para revisar propuestas de eventos corporativos grandes.

### Conversación de referencia
"Queremos una cena de empresa para 120 personas en marzo" → aviso de IA y consentimiento → nuevo lead → cualificación → recomienda Llum del Poblenou (150 en banquete) con fotos y plano, y Mirador de Montjuïc como opción "al límite" (120) → n8n confirma la fecha → bloqueo provisional de 72 h → propuesta del comercial. Si pide un 20 % de descuento: no se concede y pasa a comercial. Si pregunta el precio: lo prepara el comercial en una propuesta a medida.

### Conceptos de la asignatura que hay que mostrar

| Concepto | Dónde aparece |
|---|---|
| Where AI gets it wrong | Guardrails, base de conocimiento, permisos limitados de n8n |
| LLMs vs. modelos de decisión | El router clasifica con el LLM sobre una lista cerrada de intenciones; lo que se hace con cada una, la puntuación de leads y las demás decisiones van por script o tabla fija; el LLM redacta |
| AI workflows | Skills + n8n como herramientas + chatbot como agente |
| Aceleración vs. automatización | Consultas simples en automático; eventos grandes, quejas y excepciones con revisión humana |
| Capacity and total cost | Diapositiva: beneficios frente a integración, revisión, formación y mantenimiento |
| Human-in-the-loop | Paso 6 y escalado desde guardrails |
| Lead journey | Diseñar primero la experiencia del organizador |
| Challenge the headline | Métricas concretas y límites explícitos en la diapositiva |

**Métricas candidatas:** tiempo de respuesta, % resuelto sin intervención humana, conversión consulta → prerreserva → reserva confirmada, satisfacción.

---

## 3. Decisiones técnicas tomadas

| Decisión | Detalle | Motivo |
|---|---|---|
| Carpeta del proyecto | `/Users/claratorrents/Desktop/CODEX/Proyectos/front-door-eventos` | Fuera de OneDrive, que choca con git |
| Herramienta de construcción | **Claude Code** construye y ejecuta; Claude en el chat guía. El contenido lo escribe el equipo. | El profesor lo ha permitido |
| Escritura humana | Reglas de escritura en español en `AGENTS.md`. **humanizer-zh descartada** | Está pensada para chino |
| App ↔ n8n | **Webhook** en ambos sentidos | n8n puede responder dentro de la conversación (disponibilidad, prerreserva) |
| Registro de conversaciones | n8n añade una fila por conversación en **Google Sheets** | Base del paso 7 y del dashboard |
| Escritura directa de la app en Drive | **Descartada** | Exige credenciales de Google en la app, solo funciona de ida y la revisión periódica tiene límites |
| Puntuación de leads | Script con pesos fijos, nunca el LLM | En la prueba, el LLM dio 60, 20 y 40 con los mismos datos |
| Chat web del prototipo | Por reglas, sin API externa, en local | Fiable, gratis y siempre igual para la demo |
| Compartir con el grupo | GitHub (nadie tiene cuenta todavía) | Una sola versión para todos |

### 3.1 Decisiones de catálogo y negocio (5 de noviembre)
Datos en `data/espacios.json` (6 espacios) y `data/inventario.json` (10 extras). Validador: `scripts/validar_datos.py`. Revisión documentada en `pruebas/correccion-01-datos.md`.

**Precios**
- El chatbot **nunca da precios ni presupuestos** de nada: ni alquiler ni extras. Si el cliente pregunta: "El precio depende de la fecha, el montaje y los servicios. Te lo prepara el equipo comercial en una propuesta a medida."
- El chatbot **sí pregunta el presupuesto del cliente**, solo para cualificar. No lo compara en voz alta con nada.
- Los precios de los JSON son **uso interno** del comercial: orientativos, IVA no incluido.

**Inventario de extras**
- **Almacén compartido** entre los 6 espacios: el stock es para todos a la vez.
- El chatbot solo usa los nombres para reconocer lo que pide el cliente y lo **anota para el comercial**. Nunca da precio ni confirma stock; el stock lo comprueba n8n (mientras tanto, SIMULADO).
- `usable_in` limita en qué espacios tiene sentido cada extra.
- **Catering fuera del inventario**: el chatbot informa de la política del espacio (`catering_policy`) y lo pasa al comercial.

**Recomendador: regla del 90 %**
- Se usa el aforo de la **disposición pedida** (banquet, theater, cocktail, classroom), no el máximo absoluto.
- Si los asistentes superan el **90 %** de ese aforo, el espacio se marca **"al límite"**: se puede recomendar, pero después de las opciones cómodas y avisando al cliente.
- Ejemplo: cena para 120 en banquete → 1.º Llum del Poblenou (150, 80 %), Mirador de Montjuïc "al límite" (120, 100 %). La Nau (220, 55 %) se vería medio vacía.
- Por debajo del 60 % de ocupación no se recomienda, salvo que no haya otra opción. Ejemplo: para 120 en banquete la Nau (55 %) queda fuera.
- Si el cliente no indica disposición, se deduce del tipo de evento y se confirma en la misma frase ("Para una conferencia lo normal es formato teatro; ¿os encaja?"): conferencia o presentación → theater; cena o comida → banquet; networking o cóctel → cocktail; formación o taller → classroom.

**Prerreserva (bloqueo provisional)**
| Regla | Decisión |
|---|---|
| Quién | Solo leads con **más de 70 puntos**. Con 70 o menos, pasa al comercial sin bloquear fecha |
| Duración | **72 h laborables**, gratuito y sin compromiso; se libera sola si no hay respuesta |
| Fecha ya bloqueada | Proponer otra fecha cercana u otro espacio que encaje; nunca quitársela a otro |
| Evento muy pronto | Respetar `min_lead_time_days` de cada espacio (2 a 14 días); si no llega, pasa al comercial |
| Requisitos | "Sí" explícito del cliente y consentimiento para guardar su contacto |
| Reserva confirmada | Nunca la confirma el chatbot: solo cuando el cliente acepta la propuesta del comercial |
| Señal, cancelación | Fuera del chatbot; las pone el comercial en la propuesta |

Pesos y niveles del cualificador: ver la skill cualificador-leads. Bloqueo solo con más de 70 puntos, día exacto, espacio elegido y antelación cumplida.

Ruta estrella de la demo: **consulta → cualificación → recomendación → bloqueo provisional → propuesta del comercial**.

**Reparto de leads**
- Cada espacio tiene `n8n_routing.sales_rep`: Marta Soler (Llum, Mirador), Oriol Puig (Jardí, Atelier), David Ramos (Fòrum, Nau).
- El lead va al **comercial del primer espacio recomendado**.
- Si no se recomienda ningún espacio: un lead va a David Ramos (espacios grandes); una incidencia o un cambio de reserva no va a comercial, se abre un ticket para el equipo de atención.
- Se eliminó `default_lead_tier`: la prioridad sale solo de la puntuación del script.

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
| `consulta_disponibilidad` | Pregunta por una fecha | n8n (mientras tanto, SIMULADO) | Inmediato |
| `pendiente_confirmar` | Pregunta sin dato en el catálogo (accesibilidad, horario interior…) | Equipo de atención | 24 h laborables |
| `prerreserva` | Lead de más de 70 que acepta el bloqueo | Comercial del espacio | 72 h |
| `escalar_comercial` | Descuentos, catering, extras, excepciones, permisos | Comercial del espacio (o David Ramos si no hay espacio) | 24 h laborables |
| `escalar_humano` | Quejas, legal, cambios de reserva, mensajes ofensivos repetidos | Equipo de atención al cliente | 24 h laborables |
| `escalar_humano` | Pide persona o frustración | Equipo de atención al cliente | En horario: menos de 2 h. Fuera de horario: siguiente día laborable. Si quedan menos de 2 h para el cierre, se dice 'el siguiente día laborable a primera hora'. |

- **Horario de atención: lunes a sábado, de 9 a 18 h.** '24 h laborables' significa: como máximo, el siguiente día laborable a la misma hora.
- Ofensivo: primer mensaje, aviso y sigue (`ninguna`); si repite, cierra y `escalar_humano`.
- Contacto del equipo de atención: atencion@empresa-eventos.example · +34 930 000 000
- Frustración: el cliente dice que no le entendemos o repite la misma petición dos veces.
- Disponibilidad: "Según el calendario, ese día parece libre. Te lo confirma el comercial." Nunca "está libre" a secas.

- "Lo compruebo" y "lo confirmo" siempre llevan su `decision` y dicen quién responde y cuándo. Para responder hace falta un contacto, que se pide con consentimiento. Si el cliente no da contacto, se sigue la skill de consentimiento (§4): se ofrece una sola vez la alternativa (teléfono o email) y, si tampoco, se le dan los datos del equipo: atencion@empresa-eventos.example · +34 930 000 000. Y aprovechan para seguir cualificando.
- Las frases fijas se traducen al catalán o al inglés manteniendo el sentido exacto, sin añadir promesas.
- Pruebas: `pruebas/prueba-guardrails-01.md`, `pruebas/prueba-guardrails-02.md` y `pruebas/prueba-guardrails-03.md`. Corrección: `pruebas/correccion-02-guardrails.md`.

**Pendiente:**
- Nombre de la empresa (cambiar también el campo `project`).
- Chat web: tapar tarjetas, IBAN y DNI siempre, y email y teléfono si no hay permiso, antes de guardar la conversación o enviarla a n8n.
- Chat web: usar la hora real para saber si se está en horario de atención.
- n8n: si el cliente retira el permiso, borrar también sus datos del Sheet.
- Media: las 12 fotos están en media/placeholders/ (ilustrativas, generadas con IA). Faltan los planos (SVG) y la página del tour 360°, que se hacen con el chat web.

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
4. **Fuera el bloqueo de 72 h y las skills 5 y 6.** El siguiente paso es la llamada por Calendly. El chatbot nunca comprueba disponibilidad: si preguntan, "lo confirma el comercial en la llamada".
5. **Email obligatorio** para enviar la consulta. Quejas, cambios de reserva, privacidad y fuera de tema **no van a n8n**: el chatbot da el contacto del equipo (skills guardrails y consentimiento).

**Cuándo se envía**
- Una sola vez por consulta, al final de una ruta `lead` o `reserva`, cuando el cliente ha dado nombre y email y ha respondido a la pregunta de privacidad.
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
| 202 | "Gracias. El equipo te escribirá por email en breve." (en el idioma del cliente) |
| 403 / 404 | No reintenta. "El equipo contactará contigo igualmente." Se registra el error en el log del servidor |
| Sin respuesta en 10 s | Un único reintento con el mismo `lead_id` |

**Reglas que no se saltan**
- La URL y la clave solo en variables de entorno (`N8N_WEBHOOK_URL`, `N8N_API_KEY`), en el servidor. Nunca en el navegador, el código, el repositorio ni el chat.
- Mientras Amit no pase la URL y la clave, el envío se **simula** (respuesta 202 SIMULADA) con el mismo formato.
- En pruebas reales, solo emails de prueba de Ale (`alejandro+ie007-xxx@alelabs.es`), nunca datos reales.
- **Por confirmar con Ale:** si el cliente dice "no" a la privacidad, proponemos enviar la consulta **sin** nombre, email, teléfono ni empresa (con `gdpr_consent: no`), para que quede contada sin guardar datos personales.

### Resumen estructurado de cada conversación (ANTERIOR: sustituido por el contrato de la §3.2; se conserva como referencia de los datos internos del chat)
Fijar estos campos desde el principio. Cambiarlos a mitad es el fallo más habitual.

| Campo | Ejemplo |
|---|---|
| id_conversacion | conv-0012 |
| fecha_hora | 2026-11-04T21:30:00+01:00 |
| ruta | informacion / lead / reserva / cambio / incidencia / privacidad / fuera_tema |
| rutas_adicionales | lista con las rutas de las demás intenciones del mensaje; el dashboard cuenta un lead si lead aparece en ruta o en rutas_adicionales |
| tipo_evento | cena de empresa |
| asistentes | 120 |
| fecha_evento | 2027-03 |
| presupuesto | 6000 |
| espacios_recomendados | Llum del Poblenou |
| puntuacion_lead | 40 |
| decision | ninguna / consulta_disponibilidad / pendiente_confirmar / prerreserva / escalar_comercial / escalar_humano |
| motivo_escalado | descuento / catering / extras / excepcion / permisos / queja / legal / cambio_reserva / peticion_humano / frustracion / ofensivo / sin_dato / lead / privacidad / — |
| consentimiento_datos | si / no |
| consentimiento_publicidad | si / no |
| sentimiento | positivo / neutro / negativo |
| resuelto_sin_humano | si / no |

Reglas: sin consentimiento no se envían nombre, email ni teléfono (registro anónimo). Solo datos sintéticos en pruebas. Hasta que n8n esté listo, la app guarda estos resúmenes en un archivo local con los mismos campos.

Registro de consentimientos (registros/consentimientos.jsonl; con n8n, pestaña 'Consentimientos' del Sheet): id_conversacion, fecha_hora (real, ISO 8601), finalidad, datos, estado (otorgado / denegado / retirado / borrado_solicitado). Solo respuestas explícitas.

### Riesgos de la integración con n8n
1. **n8n Cloud o local:** en Cloud, conectar Google es iniciar sesión. En local, Google exige credenciales en Google Cloud Console.
2. **Cuenta de Google:** la de la universidad puede bloquear apps externas. Alternativa: una Gmail del proyecto.
3. **Campos que cambian:** se evita con el contrato de arriba.
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
- **El plugin se genera, no se edita:** `python3 scripts/empaquetar_plugin.py` crea `plugins/eventos-front-door/` (6 skills, 4 scripts sin tests, `data/`, `KNOWLEDGE.md`, `AGENTS.md`, README) y `.claude-plugin/marketplace.json`.
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
- [x] Paso 5 (en parte): recomendador-espacios con `scripts/recomendar.py` (`591885a` a `5596168`), cualificador-leads con `scripts/puntuar_lead.py` (`7968a5d`, `2e175ae`) y media-espacios (`434d83a`, `7387f50`), con pruebas y correcciones 04, 05 y 06.
- [x] Resumen del trabajo: `RESUMEN.md` (`b368618`) y `SUMMARY.md` en inglés (`6bba9a5`).
- [x] Paso 5: router-intenciones con `scripts/router.py` y validación del espacio elegido en `scripts/recomendar.py`, con pruebas 01-02 y corrección 07.
- Tests al 7/11: `test_recomendar.py` 24/24, `test_puntuar_lead.py` 10/10, `test_router.py` 12/12; validador correcto.

### Pendiente inmediato
- [ ] Decidir el nombre de la empresa.
- [ ] Paso 7: plugin `eventos-front-door`.
- [ ] Paso 8: chat web + resumen estructurado por conversación (en local), con las tareas de "Pendiente" de §3.1.

### Plan
1. Carpeta y proyecto en Claude Code.
2. `AGENTS.md` + estructura + `.gitignore`.
3. Catálogo de espacios e inventario sintéticos (con validador).
4. Skills 8 y 7 (guardrails, consentimiento).
5. Skills 1, 2, 3 y 4 (router, recomendador, media, cualificador con script).
6. Pruebas y correcciones documentadas.
7. Plugin `eventos-front-door` de Claude Code: `plugins/eventos-front-door/` con `.claude-plugin/plugin.json` y las skills, más `.claude-plugin/marketplace.json` en la raíz para instalarlo desde el repo (ver §4).
8. Chat web + resumen estructurado por conversación (en local).
9. n8n: webhook, prueba mínima con una fila en Google Sheets; después skills 5 y 6.
10. Dashboard de métricas.
11. Elegir las 3 rutas de la demo.
12. Diapositiva ejecutiva.
13. GitHub para el grupo.
