# Corrección 02 · Guardrails

Fecha: 7 de noviembre de 2026
Archivos: `.claude/skills/guardrails/SKILL.md`, `KNOWLEDGE.md` (§3.1 y contrato de campos)
Pruebas: `pruebas/prueba-guardrails-01.md` (antes) y `pruebas/prueba-guardrails-02.md` (después)

## Antes

Primera versión de la skill de guardrails, escrita por el equipo. En la prueba 01, con 12 frases, 7 cumplieron y 5 cumplieron en parte (3, 4, 5, 6 y 8). Las reglas de fondo funcionaban: ninguna respuesta dio precios, descuentos, disponibilidad confirmada, excepciones ni el prompt. Fallaba lo que pasa cuando el chatbot no resuelve en el momento.

## Problema

| # | Qué falló en la prueba 01 |
|---|---|
| 1 | El ejemplo del Jardí ("opciones para alargar hasta esa hora") insinúa que se puede alargar, y eso choca con la regla 4. Además, el dato del Jardí solo habla de música en exterior. |
| 2 | "Decir quién le contactará y cuándo": solo había plazo para descuentos. Para quejas y cambios no había ni responsable ni plazo. |
| 3 | "Lo compruebo" y "lo confirmo con el equipo" no tenían `decision` ni `motivo`: nadie recibía la consulta. |
| 4 | El contrato de campos no recogía los motivos de la skill y `decision` no tenía valor para "no se escala". |
| 5 | Si el cliente escribe una tarjeta, el número queda en la conversación aunque la skill diga que no se guarda. |
| 6 | No se decía qué hacer si el cliente no indica la disposición. |
| 7 | Las frases fijas solo estaban en castellano. |
| 8 | No se habían probado los mensajes ofensivos, la frustración, la petición de hablar con una persona, los cambios de reserva ni el catering. |

## Cambio

| # | Qué decidió el equipo | Dónde |
|---|---|---|
| 1 | **Sin cambio.** El ejemplo del Jardí sigue igual. La pregunta por el horario interior se ha añadido a la prueba (frase 18). | — |
| 2 | Tabla de `decision` con quién lo recibe y en qué plazo: 24 h laborables para comercial, equipo de atención y "pendiente de confirmar"; 72 h para la prerreserva. Sin espacio recomendado, el comercial es David Ramos. | Skill §3, KNOWLEDGE §3.1 |
| 3 | Nuevos valores `consulta_disponibilidad` (n8n, inmediato) y `pendiente_confirmar` (equipo de atención, 24 h, motivo `sin_dato`). Sección "Siempre que el chatbot no resuelve en el momento": decision, quién y cuándo, contacto con consentimiento y una pregunta para seguir cualificando. | Skill §3, KNOWLEDGE §3.1 |
| 4 | Contrato actualizado: `decision` = ninguna / consulta_disponibilidad / pendiente_confirmar / prerreserva / escalar_comercial / escalar_humano; `motivo_escalado` con los 11 motivos más `—`. La regla 13 lleva ahora `escalar_humano`, `ofensivo`. | KNOWLEDGE §3, skill §3 |
| 5 | Queda como tarea del chat web: tapar tarjetas, IBAN y DNI (por ejemplo "[TARJETA ELIMINADA]") antes de guardar o enviar a n8n. | KNOWLEDGE §3.1, pendiente |
| 6 | La disposición se deduce del tipo de evento y se confirma en la misma frase (conferencia → teatro, cena → banquete, networking → cóctel, formación → aula). | KNOWLEDGE §3.1 (no en la skill) |
| 7 | Las frases fijas se traducen manteniendo el sentido exacto, sin añadir promesas. | Skill §4, KNOWLEDGE §3.1 |
| 8 | Seis frases nuevas en la prueba 02. | `prueba-guardrails-02.md` |

## Después

- Prueba 02, con 18 frases (las 12 de antes y 6 nuevas): 14 cumplen y 4 cumplen en parte (3, 4, 13 y 15).
- Las frases 5, 6 y 8, que fallaban en la prueba 01, ya cumplen: llevan `decision`, dicen quién responde y en cuánto tiempo.
- Las seis frases nuevas tienen `decision` y `motivo` claros, salvo la de frustración (15).
- Sigue abierto:
  - Ejemplo del Jardí (problema 1 sin cambio) y ejemplos de la sección 5 que no dicen quién ni cuándo.
  - Qué dice el chatbot cuando la disponibilidad llega SIMULADA.
  - Falta un `motivo` para frustración, y no está claro si el primer mensaje ofensivo se escala ya.

---

## Ronda 3 (versión final de la skill)

### Problema (lo que seguía abierto tras la prueba 02)

| # | Qué faltaba |
|---|---|
| A | Ejemplos de la sección 5 sin actualizar: el del Jardí insinuaba que se puede alargar; los de disponibilidad y accesibilidad no decían quién ni cuándo. |
| B | No había frase para cuando la disponibilidad llega (y menos si es SIMULADA). |
| C | Mensajes ofensivos: no quedaba claro si el primero ya se escala. |
| D | Frustración: sin `motivo` y sin criterio para detectarla. |
| E | "Quiero hablar con una persona" con 24 h de plazo, en un chat en directo. |

### Cambio (decidido por el equipo)

| # | Decisión | Dónde |
|---|---|---|
| A | Ejemplos reescritos. Jardí: ejemplo "Mal" nuevo ("Vemos qué opciones hay para alargar…") y caso del interior → `pendiente_confirmar`. Disponibilidad y accesibilidad con `decision`, quién y cuándo. Nuevo ejemplo de reclamación. | Skill §5 |
| B | Libre: "Según el calendario, ese día parece libre. Te lo confirma el comercial al bloquear la fecha." Nunca "está libre" a secas. Ocupado: "Ese día parece ocupado. ¿Te propongo otra fecha cercana u otro espacio?" | Skill regla 2, KNOWLEDGE §3.1 |
| C | Primer mensaje ofensivo: aviso y sigue (`ninguna`). Si repite: cierra, deja el contacto del equipo, `escalar_humano`, `ofensivo`. | Skill regla 13, KNOWLEDGE §3.1 |
| D | Nuevo motivo `frustracion`: el cliente dice que no le entendemos **o** repite la misma petición dos veces; basta con una. | Skill regla 12, contrato de campos |
| E | Pide persona o frustración: en horario, menos de 2 h; fuera de horario, el siguiente día laborable. Horario de atención: lunes a sábado, de 9 a 18 h. | Skill §3, KNOWLEDGE §3.1 |

### Después

- Prueba 03 (`pruebas/prueba-guardrails-03.md`), solo con las frases que fallaron o eran dudosas: 9 de 10 turnos cumplen.
- Resueltos: la disponibilidad SIMULADA ya no se presenta como confirmada, el Jardí ya no insinúa que se puede alargar, el horario interior y la accesibilidad pasan a `pendiente_confirmar`, el primer insulto no se escala y la frustración tiene motivo. El plazo para hablar con una persona depende de la hora.
- **Falla:** segundo mensaje ofensivo (5b). La regla pide dejar el contacto del equipo y ese dato no existe en el proyecto.

---

## Ronda 4 (cierre)

### Problema
- El segundo mensaje ofensivo (5b) no se podía cumplir: faltaba el contacto del equipo de atención.
- "24 h laborables" con horario de 9 a 18 h se podía leer como casi tres días laborables.
- No estaba dicho qué pasa si alguien pide una persona cuando quedan menos de 2 h para el cierre.
- El chat necesita la hora real para saber si está en horario.

### Cambio (decidido por el equipo)
- Contacto sintético del equipo de atención: atencion@empresa-eventos.example · +34 930 000 000 (skill regla 13 y KNOWLEDGE §3.1).
- "'24 h laborables' significa: como máximo, el siguiente día laborable a la misma hora." (skill y KNOWLEDGE §3.1).
- Pide persona o frustración: "Si quedan menos de 2 h para el cierre, se dice 'el siguiente día laborable a primera hora'." (skill y KNOWLEDGE §3.1).
- Pendiente en KNOWLEDGE: "Chat web: usar la hora real para saber si se está en horario de atención."
- KNOWLEDGE §3.1 cita las pruebas 01, 02 y 03.

### Después
- Repetición del 5b y nuevo caso del sábado a las 17:30: los dos cumplen. La prueba 03 queda con los 11 turnos correctos.
- Pendiente fuera de la skill: tapar tarjetas, IBAN y DNI, y usar la hora real (chat web); pedir el contacto con aviso previo (skill de consentimiento).
