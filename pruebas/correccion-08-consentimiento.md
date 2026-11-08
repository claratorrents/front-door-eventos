# Corrección 08 · Consentimiento

Fecha: 8 de noviembre de 2026
Archivo: `.claude/skills/consentimiento/SKILL.md`: versión 2 (md5 `88a4f21318fd223bf922ccb24134ef08`, con los ajustes posteriores a la prueba 02) → versión 3 (md5 `8e3e9d1a43b5524995b327ea2a697cfe`), escrita por el equipo.
Motivo: integración con el flujo de n8n de Ale (`KNOWLEDGE.md` §3.2). Punto 2 del paso 2 de la integración.
Pruebas: `pruebas/prueba-consentimiento-02.md` (antes) y `pruebas/prueba-consentimiento-03.md` (después).

## Antes

La versión 2 estaba pensada para un chat que respondía él mismo a cada caso:
- **Cuándo pedir el contacto:** en la prerreserva, en las preguntas pendientes de confirmar y en cualquier escalado.
- **Qué datos:** nombre y un contacto, email o teléfono a elegir. Si rechazaba uno, se le ofrecía el otro una vez.
- **Permiso:** "¿Me das permiso para guardar tu nombre y tu email solo para responder a esta consulta?"
- **Publicidad:** al final, después de la prerreserva o del escalado, y solo si había dado un contacto.
- **Registro:** cada respuesta explícita, en `registros/consentimientos.jsonl` (con n8n, en una pestaña "Consentimientos" del Sheet).
- **Borrar datos de antes:** se pedía el email o teléfono para localizarlos y se escalaba al equipo (`escalar_humano`, `privacidad`), con 24 h laborables.

## Problema

Con la §3.2, varias partes ya no tenían sentido:

| # | Qué choca con la §3.2 | Decisión |
|---|---|---|
| 1 | No hay prerreserva ni escalados con respuesta del chat: la única salida de una consulta es el envío a n8n al final | 4, 6 y 7 |
| 2 | El envío necesita nombre y **email**: con solo teléfono no se puede enviar | 5 |
| 3 | El contrato pide `gdpr_consent` y `marketing_consent` (yes/no) en cada envío, antes de enviar; el flujo de Ale habla de aceptar la política de privacidad | Contrato |
| 4 | Queja, cambio, privacidad y fuera de tema no van a n8n: pedir datos para que "alguien responda" deja al cliente esperando algo que ningún canal lleva | 5 y 7 |
| 5 | La hoja de Ale no tiene pestaña de consentimientos; el consentimiento queda en Enquiries con la conversación | Contrato |
| 6 | No se prometen plazos en horas | Respuesta 5 del 8 de noviembre |

## Cambio (versión 3, del equipo)

| Parte | Versión 2 | Versión 3 |
|---|---|---|
| §2 Cuándo | Prerreserva, pendiente de confirmar y escalados | **Solo al final de una consulta de evento** (ruta `lead`), para enviarla a n8n. Fuera de una consulta no se piden datos: se da el contacto del equipo con su horario |
| §3 Qué datos | Nombre y email **o** teléfono | **Nombre y email obligatorios**; teléfono opcional; empresa si es corporativo |
| §4 Permiso | "¿Me das permiso para guardar…?"; alternativa de contacto una vez | Datos y permiso en el mismo mensaje, mencionando la política de privacidad → `gdpr_consent`. Si dice que no: se envía sin datos personales (por confirmar con Ale). Si solo da teléfono: no se envía y se le da el teléfono del equipo |
| §5 Publicidad | Al final, tras prerreserva o escalado | Una sola vez, justo después del "sí" a la privacidad y **antes del envío** → `marketing_consent` |
| §6 Registro | `registros/consentimientos.jsonl` con un apunte por respuesta | El consentimiento viaja en el envío a n8n. En `registros/conversaciones.jsonl` solo sí/no, sin datos personales. `consentimientos.jsonl` queda sustituido |
| §7 Conservación | 12 meses (leads sin reserva); datos anónimos sin límite | La frase de los 12 meses, sin más |
| §8 Retirar, ver o borrar | Retirar: se cumple al momento. Borrar datos de antes: se piden datos para localizarlos y `escalar_humano`, 24 h | Retirar antes del envío: se envía como un "no". Después del envío, o ver o borrar: contacto del equipo, **sin plazos** y sin pedir datos |
| Descripción | "…y cómo se registra" | "…y qué se envía a n8n"; se usa al final de una consulta, antes del envío |

## Después

`pruebas/prueba-consentimiento-03.md`, 7 casos:

| Caso | gdpr_consent | marketing_consent | Nombre y email | ¿Cumple? |
|---|---|---|---|---|
| a) Acepta privacidad y publicidad | yes | yes | sí | Sí |
| b) Acepta privacidad, no contesta a la publicidad | yes | no | sí | Sí |
| c) "No" a la privacidad | no | no | no | Sí |
| d) Solo teléfono | no se envía | no se envía | no | Sí |
| e) Email al principio + precio | yes | no | sí | Sí |
| f) "Borrad mis datos" sin consulta | no se envía | no se envía | no se piden | Sí |
| g) Acepta y retira el email antes del envío | no | no | no | Sí |

**Queda abierto** (la skill no lo resuelve; comentarios de la prueba 03):
1. Qué `marketing_consent` se envía cuando no hay "sí" a la privacidad. En la prueba: `no`.
2. Qué pasa si el cliente se va sin contestar a la publicidad: cuánto se espera y si se envía igual. Encaja mejor en la skill de envío a n8n.
3. Qué dice el chatbot con el 202 cuando el cliente dijo "no". La frase de la §3.2 ("te escribirá por email") sería falsa.
4. Qué se tapa en `conversation` sin consentimiento. El Pendiente de §3.1 cubre email y teléfono, pero no nombre ni empresa.
5. Solo teléfono frente a "no": el que acepta y da teléfono no llega a nadie, y el que lo rechaza todo sí se envía.
6. La frase fija de §4 no prevé que el email ya se haya dado (caso e).
7. El campo "resuelto" del registro anónimo no está definido.
