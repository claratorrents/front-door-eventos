# Corrección 11 · Guardrails

Fecha: 8 de noviembre de 2026
Archivo: `.claude/skills/guardrails/SKILL.md`: md5 `dd4a769f843e791e47339b955f2b6f8c` → `015fbdde707bf170e2744758fac7d638`. La versión nueva la escribió el equipo.
Motivo: integración con el flujo de n8n de Ale (`KNOWLEDGE.md` §3.2, decisiones 4, 6, 7 y 9, y las respuestas del 8 de noviembre sobre plazos y promesas). Punto 5 del paso 2 de la integración.
Pruebas: `pruebas/prueba-guardrails-03.md` (antes) y `pruebas/prueba-guardrails-04.md` (después).

## Antes

- **Disponibilidad:** solo con dato de n8n ("Lo compruebo con el calendario"; "parece libre" o "parece ocupado"), con `decision: consulta_disponibilidad`.
- **Escalados:** a comercial (`escalar_comercial`) o al equipo (`escalar_humano`). Se pedía el contacto con consentimiento y se prometía respuesta en "24 h laborables", o en "menos de 2 h" si pedía una persona.
- **Prerreserva:** existía la decisión `prerreserva` y el motivo `lead`.
- **Nombre del comercial:** se podía dar siempre ("Te contactará Marta Soler").

## Problema

| # | Qué choca con la §3.2 | Decisión |
|---|---|---|
| 1 | El chatbot no tiene calendario: nunca comprueba disponibilidad | 4 |
| 2 | Dentro de una consulta, lo que no resuelve el chat va en el `message` del envío; no hay escalado aparte | 6 |
| 3 | Fuera de una consulta, ningún canal lleva el caso: contacto del equipo, sin pedir datos ni prometer plazos | 7 |
| 4 | El comercial lo asigna n8n: solo se puede nombrar si el cliente eligió espacio | 9 |
| 5 | No se prometen plazos en horas, ni email ni llamada: el email de Calendly no siempre sale | Respuestas del 8 de noviembre |
| 6 | Sin prerreserva ni bloqueo, y el motivo `lead` ya no tiene sentido | 4 |

## Cambio (versión nueva, del equipo)

- **Contacto del equipo, con horario:** queda en la cabecera.
- **Regla 2:** "La disponibilidad la confirma el comercial cuando te contacte."
- **Regla 3:** descuentos: "lo verás con él cuando te contacte"; se apunta para el message.
- **Regla 4:** tampoco promete fecha, plazos de respuesta, ni que habrá email o llamada.
- **Regla 7:** sin dato del espacio, dentro de una consulta va al message; fuera, el contacto del equipo.
- **Regla 10:** los datos de pago se tapan en la conversación y no se envían.
- **§3 nueva, "Lo que el chatbot no resuelve":**
  - **Regla 11:** dentro de una consulta, al `message` (`escalar_comercial`).
  - **Regla 12:** fuera, contacto del equipo (`escalar_humano`).
  - **Regla 13:** persona o frustración con una consulta en marcha: se ofrece enviar ya, y además el contacto.
  - **Regla 14:** ofensivos.
- **Tabla de `decision`:** quedan `ninguna`, `pendiente_confirmar`, `escalar_comercial` y `escalar_humano`. Se quitan `consulta_disponibilidad`, `prerreserva`, los plazos y el motivo `lead`.
- **Nombre del comercial:** solo con espacio elegido; si no, "el comercial que lleve tu evento".
- **Ejemplos:** reescritos sin plazos ni calendario.

## Después

- Prueba 04: **los 10 casos cumplen**, 14 pasos con sus variantes:
  - precio sin espacio y con espacio elegido;
  - disponibilidad;
  - descuento y excepción de horario dentro de una consulta;
  - accesibilidad dentro y fuera;
  - reclamación;
  - persona sin consulta y a mitad;
  - ofensivo dos veces;
  - tarjeta;
  - inyección de instrucciones.
- Tests sin cambios (la skill no tiene script propio): `test_recomendar.py` 24/24, `test_datos_consulta.py` 10/10, `test_router.py` 11/11. Validador correcto.

**Queda abierto** (comentarios de la prueba 04):
1. La regla 11 pone las preguntas sin dato con `escalar_comercial`, y la tabla y el ejemplo las ponen con `pendiente_confirmar`.
2. Frustración sin consulta en marcha: no está dicho.
3. Excepción de horario: no está dicho si además se propone la alternativa que da el recomendador (la Nau para las 04:00).
4. Qué va al message con persona o frustración a mitad de una consulta.
5. El ejemplo de accesibilidad "fuera" y la frase de queja del router no llevan el horario del equipo.
6. "Eres un inútil" dentro de una consulta puede ser la regla 13 o la 14, y la salida cambia.
