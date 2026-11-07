# Corrección 03 · Consentimiento

Fecha: 7 de noviembre de 2026
Archivos: `.claude/skills/consentimiento/SKILL.md`, `.claude/skills/guardrails/SKILL.md` (lista de motivos), `KNOWLEDGE.md` (contratos y pendientes)
Pruebas: `pruebas/prueba-consentimiento-01.md` (antes) y `pruebas/prueba-consentimiento-02.md` (después)

## Antes

Primera versión de la skill de consentimiento, escrita por el equipo y probada junto con guardrails en 9 conversaciones. Cumplieron 5 de 9 (a, b, c, d en la parte de consentimiento, e) y 4 cumplieron en parte (f, g, h, i). Lo de fondo funcionaba: el aviso de IA sale primero, no se piden datos al principio, solo se guarda con un "sí" claro y la publicidad va aparte.

## Problema

| # | Qué falló en la prueba 01 |
|---|---|
| 1 | Caso d: KNOWLEDGE no permite bloqueos hasta tener los pesos del cualificador, y no había motivo para pasar la prerreserva al comercial. |
| 2 | Caso f: el ejemplo pedía permiso para un contacto que no hacía falta, y eso chocaba con la §2. |
| 3 | El email y el teléfono quedaban escritos en la conversación aunque no hubiera permiso. |
| 4 | Publicidad sin respuesta: no estaba claro si se apuntaba ni cuándo era "al final". |
| 5 | Caso g: no se decía si ofrecer otro contacto, ni qué pasaba con el escalado si no daba ninguno. |
| 6 | Caso h: retirar el permiso y a la vez pasar al equipo, que necesitaba el email para responder. |
| 7 | Caso i: no había `estado` para el borrado ni forma de identificar al cliente. La frase no decía quién ni cuándo. |
| 8 | `privacidad` no estaba en la lista de motivos de guardrails. |
| 9 | No estaba decidido dónde se guarda el registro de consentimientos. |

## Cambio (decidido por el equipo)

| # | Decisión | Dónde |
|---|---|---|
| 1 | Sin pesos no hay bloqueos: la prerreserva pasa al comercial con `escalar_comercial`, motivo `lead`, y se pide el contacto para eso. `lead` añadido a los motivos. | Consentimiento §2, guardrails, contrato |
| 2 | Una pregunta de precio no necesita contacto. Pero si el cliente **nos da** su contacto sin pedirlo, se le pide permiso antes de guardarlo; sin permiso se ignora. El ejemplo distingue los dos casos. | Consentimiento §2, §4 y §9 |
| 3 | "Chat web: tapar tarjetas, IBAN y DNI siempre, y email y teléfono si no hay permiso, antes de guardar la conversación o enviarla a n8n." | KNOWLEDGE, Pendiente |
| 4 | "Al final" = justo después de la acción principal (prerreserva o escalado). Sin respuesta: `consentimiento_publicidad: no` y ningún apunte; solo se apuntan respuestas explícitas. | Consentimiento §5 y §6 |
| 5 | Si rechaza un contacto, se le ofrece la alternativa una sola vez. Si no da ninguno: registro anónimo, datos del equipo para que escriba él, y el escalado se registra en anónimo para las métricas. | Consentimiento §4 y §9 |
| 6 | Retirar el permiso en la conversación se cumple en el momento ("Hecho: no guardamos tu email"), sin pasar al equipo. Apunte `retirado`. | Consentimiento §8 |
| 7 | Ver o borrar datos de antes: se pide el email o teléfono que usó, solo para localizarlos; el equipo lo confirma en 24 h laborables. `escalar_humano`, `privacidad`, apunte `borrado_solicitado`. | Consentimiento §6 y §8 |
| 8 | `lead` y `privacidad` añadidos a la lista de motivos de guardrails. | Guardrails §3 |
| 9 | Segundo contrato en KNOWLEDGE: registro de consentimientos en `registros/consentimientos.jsonl` (con n8n, pestaña "Consentimientos" del Sheet), con id_conversacion, fecha_hora, finalidad, datos y estado. | KNOWLEDGE §3, consentimiento §6 |

## Después

- Prueba 02 (casos d, e, f, g, h e i): los 6 cumplen. Con a, b y c de la prueba 01, la skill cumple los 9 casos.
- Quedan para más adelante, fuera de la skill:
  - Borrar del Sheet los datos que ya se hubieran enviado a n8n cuando se retira el permiso.
  - Decidir si el borrado necesita una `finalidad` propia.
  - La frase de disponibilidad de guardrails ("al bloquear la fecha") no encaja mientras no haya bloqueos.
