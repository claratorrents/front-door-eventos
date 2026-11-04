# KNOWLEDGE.md · Proyecto Front Door de eventos

Conocimiento acumulado del proyecto: enunciado, decisiones del grupo, cómo trabajar con Codex y lecciones de la prueba. Sirve a la vez de memoria para el equipo y de contexto para cualquier agente (Codex o Claude) que trabaje en el proyecto.

Última actualización: 4 de noviembre de 2026 · Clara Torrents

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
| 2 | Aviso de IA y consentimiento antes de guardar datos | Codex |
| 3 | El router clasifica la consulta | Codex |
| 3a | Información: responde desde la base de conocimiento | Codex |
| 3b | Lead o reserva: cualifica, recomienda, comprueba disponibilidad, prerreserva | Codex + n8n |
| 3c | Incidencia o cambio: abre ticket | n8n |
| 4 | Valida, enriquece y puntúa el lead | n8n |
| 5 | Reserva hueco en calendario y avisa al equipo | n8n |
| 6 | Reunión comercial o seguimiento | Persona |
| 7 | Sentimiento y registro de cada conversación | n8n |
| 8 | Dashboard de métricas | Codex |

**Reparto técnico:** Codex construye lo que ve el usuario (chat, dashboard). n8n ejecuta el proceso por detrás (calendario, reservas, avisos, tickets, registro). Los flujos de n8n se construyen desde cero.

**Riesgos:** los chatbots están muy vistos, así que la diferencia debe venir del enrutado, la cualificación y la integración. Hay muchas rutas, así que la demo se centra en **tres**. Necesita una base de conocimiento para no inventar.

### Las 8 skills

| # | Skill | Bloque | Qué hace | Comprobación clave |
|---|---|---|---|---|
| 1 | router-intenciones | Atender | Clasifica: información, lead, reserva, cambio, incidencia | Si duda, pregunta |
| 2 | recomendador-espacios | Atender | 1 a 3 espacios según evento, asistentes, disposición y presupuesto | Solo catálogo; nunca aforo menor del pedido |
| 3 | media-espacios | Atender | Fotos, vídeos, planos, tours 360° | Solo material aprobado; si no hay, lo dice |
| 4 | cualificador-leads | Vender | Empresa, tipo, fecha, asistentes, presupuesto, urgencia; puntúa | Puntuación con **script** de pesos fijos |
| 5 | disponibilidad-inventario | Vender | Espacio y material para la fecha; alternativas | Nunca confirma sin dato real de n8n |
| 6 | gestor-reservas | Vender | Prerreserva con condiciones (señal, plazo, cancelación) | Confirmación expresa del cliente |
| 7 | consentimiento | Reglas | Aviso de IA, permiso antes de guardar, datos mínimos, publicidad aparte | Registro con fecha/hora real, finalidad e id_conversacion |
| 8 | guardrails | Reglas | Tema, tono, escalado a persona | Nunca inventa precios ni disponibilidad; nunca descuentos; quejas y legal a persona |

**Orden:** 8 → 7 → 2 → 4. Las skills 5 y 6 dependen de tener n8n conectado.

Además existe la skill **buying-committee-simulator** (ya probada, con corrección registrada): simula el comité de compra del cliente y sirve para revisar propuestas de eventos corporativos grandes.

### Conversación de referencia
"Queremos una cena de empresa para 120 personas en marzo" → aviso de IA y consentimiento → nuevo lead → cualificación → recomienda un salón de 150 en banquete con fotos y plano → n8n confirma fecha y mesas → prerreserva pendiente de confirmar. Si pide un 20 % de descuento: no se concede y pasa a comercial.

### Conceptos de la asignatura que hay que mostrar

| Concepto | Dónde aparece |
|---|---|
| Where AI gets it wrong | Guardrails, base de conocimiento, permisos limitados de n8n |
| LLMs vs. modelos de decisión | Router y cualificador deciden con reglas; el LLM redacta |
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
| Herramienta de construcción | **Pendiente de confirmar.** Recomendado: Codex construye y Claude guía | La asignatura usa Codex |
| App ↔ n8n | **Webhook** en ambos sentidos | n8n puede responder dentro de la conversación (disponibilidad, prerreserva) |
| Registro de conversaciones | n8n añade una fila por conversación en **Google Sheets** | Base del paso 7 y del dashboard |
| Escritura directa de la app en Drive | **Descartada** | Exige credenciales de Google en la app, solo funciona de ida y la revisión periódica tiene límites |
| Puntuación de leads | Script con pesos fijos, nunca el LLM | En la prueba, el LLM dio 60, 20 y 40 con los mismos datos |
| Chat web del prototipo | Por reglas, sin API externa, en local | Fiable, gratis y siempre igual para la demo |
| Compartir con el grupo | GitHub (nadie tiene cuenta todavía) | Una sola versión para todos |

### Resumen estructurado de cada conversación (contrato app → n8n → Sheets)
Fijar estos campos desde el principio. Cambiarlos a mitad es el fallo más habitual.

| Campo | Ejemplo |
|---|---|
| id_conversacion | conv-0012 |
| fecha_hora | 2026-11-04T21:30:00+01:00 |
| ruta | informacion / lead / reserva / cambio / incidencia |
| tipo_evento | cena de empresa |
| asistentes | 120 |
| fecha_evento | 2027-03 |
| presupuesto | 6000 |
| espacios_recomendados | Llum del Poblenou |
| puntuacion_lead | 40 |
| decision | prerreserva / escalar_comercial / escalar_humano |
| motivo_escalado | descuento / queja / legal / — |
| consentimiento_datos | si / no |
| consentimiento_publicidad | si / no |
| sentimiento | positivo / neutro / negativo |
| resuelto_sin_humano | si / no |

Reglas: sin consentimiento no se envían nombre, email ni teléfono (registro anónimo). Solo datos sintéticos en pruebas. Hasta que n8n esté listo, la app guarda estos resúmenes en un archivo local con los mismos campos.

### Riesgos de la integración con n8n
1. **n8n Cloud o local:** en Cloud, conectar Google es iniciar sesión. En local, Google exige credenciales en Google Cloud Console.
2. **Cuenta de Google:** la de la universidad puede bloquear apps externas. Alternativa: una Gmail del proyecto.
3. **Campos que cambian:** se evita con el contrato de arriba.
4. **Mitigación:** prueba mínima de punta a punta en cuanto haya n8n (una conversación → webhook → una fila en el Sheet).

---

## 4. Cómo funciona Codex

### Las 4 capas
| Capa | Qué es |
|---|---|
| Prompt | Lo que se pide en cada momento |
| `AGENTS.md` | Contexto permanente; Codex lo lee en cada tarea |
| Skills | `.agents/skills/<nombre>/SKILL.md`; Codex solo ve nombre y descripción y carga el resto cuando la necesita |
| Plugin | Paquete instalable con varias skills; sirve para compartir |

### Formato de una skill
```markdown
---
name: nombre-de-la-skill
description: Cuándo SÍ se usa y cuándo NO. Es lo que decide si se activa.
---
Instrucciones como comprobaciones concretas.
Ejemplos de respuesta buena y mala.
```

### Plugin
```
plugins/eventos-front-door/
├── .codex-plugin/plugin.json   ← solo este archivo dentro de .codex-plugin
└── skills/<nombre>/SKILL.md
```
- Crear: pedir a Codex `@plugin-creator`.
- Marketplace del repo: `.agents/plugins/marketplace.json`.
- Instalar: escribir `/plugins` en Codex → instalar desde el marketplace local → abrir un **chat nuevo**.
- Las skills ya funcionan dentro del proyecto sin instalar el plugin; el plugin sirve para compartir.

### Codex vs. Claude (mismos conceptos, otros nombres)
| | Codex | Claude |
|---|---|---|
| Contexto | `AGENTS.md` | `CLAUDE.md` |
| Skills | `.agents/skills/` | `.claude/skills/` |
| Formato de skill | `SKILL.md` (estándar abierto) | `SKILL.md` (mismo estándar) |

Truco: si se usan los dos, `CLAUDE.md` puede limitarse a decir "Lee AGENTS.md".

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

Pesos de la prueba para el cualificador, como punto de partida: fecha 25 · asistentes 20 · presupuesto 20 · tipo de evento 15 · empresa 10 · urgencia 10. Más de 70 → prerreserva; 70 o menos → comercial. **El grupo debe decidirlos y justificarlos.**

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
- [x] Paso 1: carpeta `front-door-eventos` creada.

### Pendiente inmediato
- [ ] Confirmar herramienta de construcción (recomendado: Codex) y abrir la carpeta en ella.
- [ ] Decidir el nombre de la empresa.
- [ ] Paso 2: `AGENTS.md` del proyecto real (con mapa, 8 skills, reparto, webhook, contrato de campos y reglas de escritura).

### Plan
1. Carpeta y proyecto en Codex.
2. `AGENTS.md` + estructura + `.gitignore`.
3. Catálogo de espacios e inventario sintéticos (con validador).
4. Skills 8 y 7 (guardrails, consentimiento) + humanizer-zh.
5. Skills 1, 2, 3 y 4 (router, recomendador, media, cualificador con script).
6. Pruebas y correcciones documentadas.
7. Plugin `eventos-front-door`.
8. Chat web + resumen estructurado por conversación (en local).
9. n8n: webhook, prueba mínima con una fila en Google Sheets; después skills 5 y 6.
10. Dashboard de métricas.
11. Elegir las 3 rutas de la demo.
12. Diapositiva ejecutiva.
13. GitHub para el grupo.
