# Resumen del proyecto · Front Door de eventos

Estado a 7 de noviembre de 2026. Sale de los archivos del repositorio y de sus 18 commits (del 4 al 7 de noviembre). Lo que no está claro se marca como **por confirmar**.

**Comprobación al escribir este resumen:**

| Comprobación | Resultado |
|---|---|
| `python3 scripts/validar_datos.py` | Todo correcto: 6 espacios, 25 elementos de media (24 aprobados), 10 artículos de inventario |
| `python3 scripts/test_recomendar.py` | **21/21** casos correctos |
| `python3 scripts/test_puntuar_lead.py` | **10/10** casos correctos |
| `borradores/` | No existe: no hay borradores pendientes |

---

## 1. Qué construimos y para quién

Un chatbot "front door" para una empresa que alquila espacios para eventos en Barcelona (nombre aún pendiente: `[EMPRESA]`). Atiende a quien entra en la web, entiende qué quiere y lo resuelve o lo pasa a la persona adecuada. Es el prototipo del máster en La Salle (asignatura *AI in Business*), que se presentará en una diapositiva para dirección. Solo datos inventados. *(Fuentes: `AGENTS.md`, `KNOWLEDGE.md` §1–2)*

Cómo trabajamos: el equipo escribe el contenido (skills, datos, textos) y Claude Code lo ejecuta, lo prueba y lo guarda. Cada commit se hace cuando el equipo lo aprueba. *(`AGENTS.md`, `KNOWLEDGE.md` §3)*

---

## 2. Estado de un vistazo

| Pieza | Estado | Dónde |
|---|---|---|
| Contexto del equipo | Hecho | `AGENTS.md` (27 líneas, 5 reglas), `CLAUDE.md` (`@AGENTS.md`), `KNOWLEDGE.md` |
| Datos: catálogo e inventario | Hecho | `data/espacios.json` (6 espacios), `data/inventario.json` (10 extras) |
| Validador de datos | Hecho | `scripts/validar_datos.py` |
| Skill 8 · guardrails | Hecho | `.claude/skills/guardrails/` |
| Skill 7 · consentimiento | Hecho | `.claude/skills/consentimiento/` |
| Skill 2 · recomendador-espacios | Hecho | `.claude/skills/recomendador-espacios/` + `scripts/recomendar.py` |
| Skill 4 · cualificador-leads | Hecho | `.claude/skills/cualificador-leads/` + `scripts/puntuar_lead.py` |
| Skill 3 · media-espacios | Hecho | `.claude/skills/media-espacios/` (usa `recomendar.py`) |
| Skill 1 · router-intenciones | Pendiente | No existe todavía |
| Skill 5 · disponibilidad-inventario | Pendiente | Depende de n8n (`KNOWLEDGE.md` §2) |
| Skill 6 · gestor-reservas | Pendiente | Depende de n8n. Parte de la prerreserva ya la cubre el cualificador (oferta del bloqueo y frase tras el "sí"); el reparto final entre las dos skills está **por confirmar** |
| Plugin `eventos-front-door` | Pendiente | No hay carpeta `plugins/` (plan en `KNOWLEDGE.md` §4 y §7) |
| Chat web | Pendiente | Plan: por reglas, en local, sin API externa (`KNOWLEDGE.md` §3) |
| n8n (webhook, Google Sheets) | Pendiente | Mientras tanto, todo lo de n8n se marca SIMULADO |
| Media real (fotos, planos, tour) | Pendiente | Hoy todo es de relleno (`illustrative: true`, rutas `/media/placeholders/`) |
| Dashboard de métricas | Pendiente | `KNOWLEDGE.md` §7, paso 10 |
| Diapositiva ejecutiva | Pendiente | `KNOWLEDGE.md` §7, paso 12 |
| GitHub para el grupo | Pendiente | Nadie tiene cuenta todavía (`KNOWLEDGE.md` §3) |

---

## 3. Decisiones clave del equipo

| Tema | Decisión | Por qué |
|---|---|---|
| Herramienta | Claude Code construye y ejecuta; el equipo escribe el contenido | El profesor lo permitió; la prueba inicial fue con Codex (`KNOWLEDGE.md` §3–4, commit `3585c67`) |
| Precios | El chatbot nunca da precios ni presupuestos; sí pregunta el presupuesto del cliente | El precio depende de fecha, montaje y servicios: lo prepara el comercial (`AGENTS.md` regla 2) |
| Disponibilidad | Nunca se confirma sin dato real de n8n; lo simulado se marca SIMULADO y nunca se presenta como confirmado | Evitar promesas falsas en la demo (`AGENTS.md`, guardrails regla 2) |
| Descuentos | Nunca se conceden ni se insinúan; pasan al comercial | Lo decide una persona (`AGENTS.md` regla 5) |
| Decidir con reglas | Recomendación, puntuación y escalados los decide un script o una tabla fija; el LLM solo redacta | En la prueba, el LLM puntuó 60, 20 y 40 con los mismos datos (`KNOWLEDGE.md` §3 y §5) |
| Regla del 90 % | Más del 90 % del aforo de la disposición pedida → "al límite": se recomienda después y avisando | No llenar un espacio hasta el último sitio sin avisar (`KNOWLEDGE.md` §3.1) |
| Regla del 60 % | Por debajo del 60 % no se recomienda, salvo que no haya otra opción. Si la única opción está al límite, se añade como alternativa el primer espacio por debajo del 60 % | Un espacio medio vacío no luce; pero el cliente debe tener alternativa (`KNOWLEDGE.md` §3.1; skill recomendador §2) |
| Prerreserva | Bloqueo provisional gratuito de 72 h laborables, solo con más de 70 puntos, día exacto, espacio elegido y antelación cumplida, y con un "sí" explícito | Solo se bloquea fecha a leads serios y concretos; la reserva final la confirma el comercial (`KNOWLEDGE.md` §3.1; skill cualificador §4) |
| Pesos del cualificador | Fecha 25 · asistentes 20 · presupuesto 20 · tipo 15 · empresa 10 · urgencia 10, con niveles fijos y una tabla de frases → nivel | Mismos pesos que en la prueba, decididos el 7/11; la tabla evita que el LLM decida el nivel (`KNOWLEDGE.md` §5; skill cualificador §2–3) |
| Escalados | 6 valores de `decision` con quién lo recibe y en qué plazo; 14 motivos de escalado (más `—`) | Que nadie se quede sin respuesta y que todo se pueda medir (`KNOWLEDGE.md` §3.1 y contrato) |
| Horario de atención | Lunes a sábado, 9–18 h. "24 h laborables" = como máximo, el siguiente día laborable a la misma hora. Si piden una persona: menos de 2 h en horario | Plazos que el cliente entienda (`KNOWLEDGE.md` §3.1) |
| Consentimiento | Aviso de IA en el primer mensaje; contacto solo cuando hace falta; permiso explícito antes de guardar; publicidad aparte, una vez; retirar el permiso se cumple en el momento | RGPD y datos mínimos (skill consentimiento) |
| Registro de consentimientos | `registros/consentimientos.jsonl` (con n8n, pestaña del Sheet), solo respuestas explícitas | Poder demostrar cada permiso (`KNOWLEDGE.md` §3) |
| Media | Solo material aprobado; foto de la tarjeta por disposición; nunca de una zona que cierra antes; nunca la ruta del archivo; "Imagen ilustrativa" si `illustrative: true` | No enseñar nada que no exista o no esté aprobado (skill media) |
| Contacto del equipo | atencion@empresa-eventos.example · +34 930 000 000 (sintético) | Hacía falta para cerrar conversaciones ofensivas y para quien no da contacto (corrección 02, ronda 4) |

---

## 4. Skills

Todas las pruebas las hizo Claude Code respondiendo **como si fuera el chatbot**, aplicando las skills y ejecutando los scripts. Todavía no hay un chat web que lo haga solo (ver §8).

### Guardrails (`.claude/skills/guardrails/SKILL.md`)
- **Qué hace:** revisa cada respuesta antes de enviarla (precios, disponibilidad, descuentos, datos internos y sensibles, aforo, políticas del espacio, tema, idioma) y decide si hay que pasar a una persona.
- **Rondas:** 3 pruebas y 4 rondas de corrección.
  - Prueba 01: 12 frases; 7 cumplen y 5 en parte.
  - Prueba 02: 18 frases; 14 cumplen y 4 en parte.
  - Prueba 03: 10 turnos; 9 cumplen. Tras la ronda 4, los 11 turnos de la repetición cumplen.
- **Qué falló y cómo se corrigió:**
  - Las respuestas de "lo compruebo" no tenían `decision`, quién ni cuándo → tabla de decisiones con responsables y plazos.
  - El ejemplo del Jardí insinuaba que se podía alargar la fiesta → ejemplo "Mal" nuevo.
  - Faltaba un motivo para la frustración → `frustracion`.
  - No estaba claro si el primer insulto se escalaba → primer insulto: aviso y sigue.
  - Faltaban el contacto del equipo y el significado de "24 h laborables" → contacto sintético y definición de "24 h laborables".
  - La frase de disponibilidad hablaba de "bloquear" cuando aún no había bloqueos → frase nueva (commit `6a11b2c`).
- **Archivos:** `pruebas/prueba-guardrails-01.md`, `-02.md`, `-03.md` · `pruebas/correccion-02-guardrails.md` · commits `e323834`, `6a11b2c`, `1d8b780`.

### Consentimiento (`.claude/skills/consentimiento/SKILL.md`)
- **Qué hace:** aviso de IA, cuándo y qué datos personales se piden, permiso antes de guardar, publicidad aparte, registro de cada permiso, y cómo retirar el permiso o borrar datos.
- **Rondas:** 2 pruebas.
  - Prueba 01: 9 conversaciones; 5 cumplen y 4 en parte.
  - Prueba 02: 6 casos repetidos; los 6 cumplen.
- **Qué falló y cómo se corrigió:**
  - La prerreserva era imposible sin pesos → pasa al comercial con motivo `lead`.
  - Se pedía permiso para un email que no hacía falta → se distingue entre pedirlo nosotros y que nos lo den.
  - No se ofrecía otro contacto si el cliente rechazaba uno → se ofrece la alternativa una sola vez.
  - Retirar el permiso se mandaba al equipo → se cumple en el momento.
  - Faltaba un estado para el borrado → `borrado_solicitado`, con finalidad propia.
  - No estaba decidido dónde se guarda el registro → segundo contrato en `KNOWLEDGE.md`.
- **Archivos:** `pruebas/prueba-consentimiento-01.md`, `-02.md` · `pruebas/correccion-03-consentimiento.md` · commits `bea7691`, `6a11b2c`.

### Recomendador de espacios (`.claude/skills/recomendador-espacios/SKILL.md`)
- **Qué hace:** recomienda de 1 a 3 espacios en tarjetas sin precio. La elección y el orden los decide `scripts/recomendar.py`.
- **Rondas:** 3 pruebas.
  - Prueba 01: 4 frases.
  - Prueba 02: 6 frases.
  - Prueba 03: 4 frases.
  - Todas cumplieron, pero cada ronda dejó puntos abiertos que el equipo cerró.
- **Qué falló y cómo se corrigió:**
  - El Jardí se trataba distinto en guardrails y en el recomendador → frase propia para el Jardí.
  - No se avisaba de la terraza del Mirador → `zone_end_times` y `avisos_zona` en el script.
  - Faltaba una frase para cuando solo hay una opción al límite → frase de "única opción" y alternativa por debajo del 60 %.
  - Un empate dependía del orden del JSON → desempate por menos aforo, comparando con fracciones exactas.
  - El "por qué encaja" lo inventaba el LLM → `event_types` por espacio.
  - Las horas eran ambiguas → regla de 1 a 7 (madrugada) y de 8 a 12 (se pregunta).
  - La ocupación podía salir en la respuesta → es un dato interno.
  - Fallo de Claude Code en la prueba 03: se olvidó del horario de la terraza al redactar → ahora lo avisa el script.
- **Archivos:** `pruebas/prueba-recomendador-01.md`, `-02.md`, `-03.md` · `pruebas/correccion-04-recomendador.md` · commits `591885a`, `edbbc78`, `72eadfe`, `5596168`.

### Cualificador de leads (`.claude/skills/cualificador-leads/SKILL.md`)
- **Qué hace:** recoge fecha, asistentes, presupuesto, tipo, empresa y urgencia, puntúa de 0 a 100 con `scripts/puntuar_lead.py` y decide entre el bloqueo provisional o pasar al comercial.
- **Rondas:** 2 pruebas.
  - Prueba 01: cena de 120 y boda; las dos cumplen.
  - Prueba 02: la cena repetida; cumple.
- **Qué falló y cómo se corrigió:**
  - No había frase tras el "sí" al bloqueo, con el riesgo de presentar como confirmado algo SIMULADO → frases fijas para simulado y para real.
  - "Unos" puntuaba distinto en asistentes y en presupuesto → siempre aproximado.
  - No se decía qué hacer si faltaban el día y el espacio → se preguntan los dos.
  - El tipo se medía siempre con el primer espacio → espacio de referencia: el elegido, si no el primero.
  - Pasar frases a niveles lo decidía el LLM → tabla fija y "este mes" calculado con la fecha real.
  - Dos plazos distintos en dos mensajes seguidos → plazos unificados (commit `2e175ae`).
- **Archivos:** `pruebas/prueba-cualificador-01.md`, `-02.md` · `pruebas/correccion-05-cualificador.md` · commits `7968a5d`, `2e175ae`.

### Media de espacios (`.claude/skills/media-espacios/SKILL.md`)
- **Qué hace:** elige la foto de cada tarjeta y enseña fotos, plano o tour 360° aprobados, sin rutas. Dice cuándo algo no existe (no hay vídeos).
- **Rondas:** 2 pruebas.
  - Prueba 01: 5 frases; las 5 cumplen.
  - Prueba 02: 6 frases; las 6 cumplen.
- **Qué falló y cómo se corrigió:**
  - "Imagen ilustrativa" no tenía dato → `illustrative` en los 25 elementos.
  - Salía la foto de la terraza cerrada o en una conferencia → `zone` y regla de interior antes que exterior.
  - El LLM buscaba la media en los datos → función `media_aprobada` en el script.
  - Faltaba una foto de teatro del Mirador → `mirador-montjuic-foto-03` (commit `7387f50`).
- **Archivos:** `pruebas/prueba-media-01.md`, `-02.md` · `pruebas/correccion-06-media.md` · commits `434d83a`, `7387f50`.

### Datos (no es una skill, pero tuvo su corrección)
- **Revisión:** se detectaron 9 incoherencias en los datos. El equipo decidió cada una; por ejemplo, el guardarropa ya no se puede usar en el Atelier y el tagline del Mirador se unificó con su `full_profile`. `pruebas/correccion-01-datos.md` · commits `7a5ebe4`, `121a83b`.

---

## 5. Scripts y tests

| Script | Qué decide | Tests |
|---|---|---|
| `scripts/validar_datos.py` | Que los datos cumplen las reglas del equipo: 6 espacios con todos los campos; aforos ordenados (cocktail > theater > banquet > classroom) y `absolute_max` igual al mayor; sin campos antiguos ni la palabra "ficticio/a"; `max_end_time` y `zone_end_times` en formato HH:MM; `event_types`; media con tipo válido, `approved`, `illustrative`, `disposition` en fotos aprobadas, y al menos una foto y un plano aprobados por espacio; inventario con stock > 0 y espacios existentes | Todo correcto con los datos reales. En cada ronda se probó con una copia con errores provocados y los detectó todos |
| `scripts/recomendar.py` | Qué espacios se recomiendan y en qué orden: aforo de la disposición, antelación, horario, grupos `comodo` / `al_limite` / `bajo_60`, orden por cercanía al 80 % con desempate, alternativa, máximo 3, descartes con motivo, avisos de zona y foto de la tarjeta. También la media aprobada por tipo (`--media`) | **21/21** (`scripts/test_recomendar.py`): los 8 casos calculados por el equipo, desempate, alternativa, aviso de zona, 6 de foto y 4 de media |
| `scripts/puntuar_lead.py` | La puntuación del lead (0–100) con los niveles de la skill; tipo según el espacio de referencia; "este mes" con la fecha real; la decisión (`prerreserva` solo si se cumplen las 4 condiciones) y qué condiciones faltan | **10/10** (`scripts/test_puntuar_lead.py`): los 5 casos del equipo (80, 90, 30, 85, 70), los 4 casos nuevos pedidos y 1 de prioridad del espacio elegido |

---

## 6. Evidencias para clase (lab sheet)

| Evidencia (`KNOWLEDGE.md` §1) | Estado | Archivo o commit |
|---|---|---|
| 1. Contexto del equipo guardado | Hecho | `AGENTS.md` (`4b17310`), `CLAUDE.md` (`5f00b31`), `KNOWLEDGE.md` |
| 2. Una skill útil, creada o encontrada | Hecho (5 skills creadas por el equipo) | Por ejemplo, guardrails (`e323834`) o cualificador (`7968a5d`) |
| 3. Skill empaquetada como plugin | **Pendiente** | No hay `plugins/` todavía. Plan en `KNOWLEDGE.md` §4 |
| 4. Tarea probada con una corrección anotada | Hecho (6 correcciones) | Por ejemplo, `pruebas/prueba-guardrails-01.md` → `pruebas/correccion-02-guardrails.md` |
| 5. Limitación conocida y lo que queda pendiente | Hecho | Comentarios de cada prueba, "Pendiente" de `KNOWLEDGE.md` §3.1 y la sección 8 de este resumen |

---

## 7. Conceptos de la asignatura aplicados

| Concepto | Ejemplo concreto del proyecto |
|---|---|
| LLMs vs. modelos de decisión | La puntuación la calcula `puntuar_lead.py` con pesos fijos, porque en la prueba el LLM dio 60, 20 y 40 con los mismos datos. La recomendación la decide `recomendar.py`; el LLM solo redacta las tarjetas |
| Human-in-the-loop | Descuentos, quejas, excepciones y permisos pasan siempre a una persona. El bloqueo necesita un "sí" explícito y la reserva final solo la confirma el comercial. En el trabajo diario, el equipo escribe cada skill y aprueba cada commit |
| Where AI gets it wrong | Las pruebas lo han mostrado varias veces. Un ejemplo de la skill insinuaba que se podía alargar una fiesta. El LLM tenía que "estirar" el porqué de una recomendación. En la prueba-recomendador-03, Claude Code olvidó el horario de la terraza. Con decimales, un empate no salía como empate. Cada caso acabó en una regla o en un script |
| Challenge the headline | "Pasar el validador no significa que los datos tengan sentido": los datos lo pasaban y aun así tenían 9 incoherencias (corrección 01). Las pruebas cuentan los cumplimientos parciales, no solo los aciertos (por ejemplo, 7 de 12 en guardrails 01). Las métricas para la diapositiva están **pendientes** |
| AI workflows | Skills que se llaman entre sí (guardrails + consentimiento + recomendador + cualificador + media), scripts como herramientas y n8n como proceso de fondo. n8n aún está simulado |
| Aceleración vs. automatización | El chatbot resuelve solo lo sencillo: información, recomendación y cualificación. El bloqueo es provisional, y el precio y la reserva final quedan en manos del comercial |
| Lead journey | La ruta estrella de la demo: consulta → cualificación → recomendación → bloqueo provisional → propuesta del comercial (probada en `pruebas/prueba-cualificador-02.md`) |
| Capacity and total cost | **Pendiente**: va en la diapositiva (`KNOWLEDGE.md` §2) |

---

## 8. Pendientes y limitaciones conocidas

**Pendiente de construir**
- Skills 1 (router-intenciones), 5 (disponibilidad-inventario) y 6 (gestor-reservas).
- Plugin `eventos-front-door`, chat web, n8n, dashboard, diapositiva y GitHub.
- Nombre de la empresa (y el campo `project` de `espacios.json`, que sigue en inglés).
- Media real: fotos generadas con IA, planos en SVG y una página para el tour 360°.

**Pendiente para el chat web y n8n** (`KNOWLEDGE.md` §3.1)
- Tapar tarjetas, IBAN y DNI siempre, y email y teléfono si no hay permiso, antes de guardar o enviar a n8n.
- Usar la fecha y la hora reales: horario de atención, "este mes" y antelación.
- Si el cliente retira el permiso, borrar también sus datos del Sheet.
- Crear `registros/consentimientos.jsonl`: aún no existe, porque no hay chat que escriba en él.

**Limitaciones conocidas**
- **Las pruebas son simuladas:** Claude Code responde como el chatbot. Aún no se ha probado con un chat real ni con un cliente real.
- **Todo lo que depende de n8n es SIMULADO:** disponibilidad, bloqueo y stock.
- **El LLM sigue traduciendo frases a niveles** (cualificador) y redactando. La tabla fija lo acota, pero no lo elimina.
- **El inventario de extras** (`data/inventario.json`) solo lo revisa el validador: aún no lo usa ninguna skill ni ningún script que decida algo.
- **Por confirmar:** si `/plugin` funciona en la app de escritorio o hace falta el terminal, y si hay que abrir una sesión nueva tras instalar (`KNOWLEDGE.md` §4).
- **Por confirmar:** la skill **buying-committee-simulator** aparece en `KNOWLEDGE.md` §2 como "ya probada", pero no está en este repositorio. Viene de la prueba anterior (`reservas-eventos`).
- **`KNOWLEDGE.md` §7 ("Estado actual") está desfasado:** sigue diciendo que el paso 4 (guardrails y consentimiento) está pendiente, y la fecha de "Última actualización" es el 5 de noviembre.
