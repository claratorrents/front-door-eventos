# Corrección 10 · Router de intenciones

Fecha: 8 de noviembre de 2026
Archivos:
- `.claude/skills/router-intenciones/SKILL.md`: md5 `835738ddcb4c892a80b23b3b45dd63f3` → `5fa77b005ebb442749577ea3c70fd4cf`. La versión nueva la escribió el equipo.
- `scripts/router.py` y `scripts/test_router.py`.
- `KNOWLEDGE.md`: valores de `ruta` del contrato anterior y §7.

Motivo: integración con el flujo de n8n de Ale (`KNOWLEDGE.md` §3.2, decisiones 5, 7 y 8). Punto 4 del paso 2 de la integración.
Pruebas: `pruebas/prueba-router-02.md` (antes) y `pruebas/prueba-router-03.md` (después).

## Antes

- **Intenciones:** 8, entre ellas `reserva` (bloquear espacio y fecha concretos), con su propia ruta `reserva`.
- **Contacto con consentimiento:** `cambio_reserva`, `queja` y `persona` escalaban a una persona y pedían el contacto con consentimiento para que les respondieran.
- **Envío a n8n:** el script no decía si la conversación acabaría en un envío.
- **`persona`:** siempre `escalar_humano`, con plazo de menos de 2 h en horario.

## Problema

| # | Qué choca con la §3.2 | Decisión |
|---|---|---|
| 1 | No hay bloqueos: `reserva` no lleva a nada distinto de `nuevo_evento`, y el espacio elegido viaja en `preferred_location` | 8 |
| 2 | Queja, cambio de reserva y persona sin consulta no van a n8n: pedir datos para que alguien responda no tiene ningún canal detrás | 5 y 7 |
| 3 | Solo la consulta de evento acaba en un envío; el resto de skills y la skill de envío necesitan saberlo | 5 |
| 4 | Persona o frustración con una consulta en marcha: se ofrece cerrar y enviar ya, y además el contacto del equipo | Respuesta 4 del 8 de noviembre |

## Cambio

**Skill (texto del equipo):**
- **Intenciones:** 7; `reserva` se junta con `nuevo_evento`.
- **Tabla con columna "¿Va a n8n?":** `cambio_reserva` y `queja` dan el contacto del equipo, sin plazos ni datos. `persona` depende de si hay una consulta en marcha.
- **§3 nueva:** quién pregunta primero dentro de un `nuevo_evento` (recomendador → tarjetas → cualificador → consentimiento y envío), con un máximo de dos preguntas por mensaje entre todas las skills.
- **§5:** prioridad sin `reserva`, y frase fija para queja + evento nuevo.

**Script (`router.py`):**
- **`reserva`:** fuera de la tabla, de la prioridad y de los valores de ruta. Si llega, da error como cualquier intención desconocida.
- **Sin consentimiento:** `cambio_reserva`, `queja` y `persona` ya no lo llevan (solo guardrails).
- **Campo `a_n8n`:** true solo para `nuevo_evento`, y para `persona` con consulta en marcha. Por mensaje, es true si alguna intención lo es (queja + evento nuevo → true).
- **Campo `accion`:**
  - `contacto_equipo` para `cambio_reserva`, `queja` y `persona` sin consulta en marcha. La tabla de la skill lo dice para las tres; me pedisteis el campo para `persona`, y lo he puesto también en las otras dos.
  - `ofrecer_envio` para `persona` con `--consulta-en-marcha`.
  - Por mensaje, la acción de la intención más prioritaria que tenga una.
- **`persona` con consulta en marcha y sin otro tema:** la ruta es `lead`, porque la consulta en marcha es un `nuevo_evento`. Antes habría sido `incidencia`. Es una interpretación mía de "la del tema".
- **Docstring:** apunta a la §5 para la prioridad.

**Tests (`test_router.py`):** los 9 esperados del equipo, más el caso antiguo de intención desconocida.

**KNOWLEDGE:** `reserva` sale de los valores de `ruta` del contrato anterior (marcado), y en §7 queda el punto 4 como hecho.

## Después

- `test_router.py`: **10/10**. Los 9 esperados del equipo pasan sin ajustes; el décimo es el caso antiguo "comprar_entradas → error".
- Resto: `test_recomendar.py` 24/24, `test_datos_consulta.py` 10/10, validador correcto.
- Prueba 03: **las 3 conversaciones cumplen**.
  - "Quiero el Mirador el 14 de marzo para 100" va como `nuevo_evento` y se valida el espacio.
  - En queja + evento nuevo, la queja va al contacto del equipo y la consulta sigue hacia n8n.
  - Con persona a mitad de una consulta se ofrece el envío y el contacto.

**Queda abierto** (comentarios de la prueba 03):
1. `recomendar.py --validar` no devuelve `avisos_zona`, y la tarjeta del Mirador necesita el aviso de la terraza. Es para el punto 6.
2. Con `ofrecer_envio`, el router no incluye consentimiento, aunque si el cliente acepta hay que hacer la pregunta de privacidad.
3. La promesa "te llegará un email para reservarla" (KNOWLEDGE §3.1) no siempre se cumple: el flujo de Ale solo envía el email con Calendly si el lead es bueno, hay fecha y hay espacio.
4. "Cerrar ya" con datos pendientes: no está escrito que se envíe sin preguntar lo que falta.
5. La §1 de la skill remite a "la prioridad de la §4", pero la prioridad está en la §5.
