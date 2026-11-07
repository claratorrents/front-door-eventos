# Corrección 07 · Router de intenciones

Fecha: 7 de noviembre de 2026
Archivos: `.claude/skills/router-intenciones/SKILL.md`, `scripts/router.py`, `scripts/test_router.py`, `scripts/recomendar.py` y `scripts/test_recomendar.py` (validación del espacio elegido), `AGENTS.md` (regla 3), `KNOWLEDGE.md` (contrato, §2 y §7)
Pruebas: `pruebas/prueba-router-01.md` (antes) y `pruebas/prueba-router-02.md` (después)

## Antes

Primera versión de la skill, escrita por el equipo. El LLM solo clasifica en una lista cerrada de 8 intenciones y `scripts/router.py` decide skills, decisión, ruta y orden. La regla 3 de `AGENTS.md` se cambió para reflejar este reparto. Los 9 tests del equipo pasaron sin ajustes y las 10 frases de la prueba 01 cumplieron, pero quedaron 5 puntos abiertos.

## Problema

| # | Qué no convencía en la prueba 01 |
|---|---|
| 1 | Una sola `ruta` por conversación perdía el lead cuando venía con otra intención más prioritaria (queja + evento nuevo, privacidad + cóctel). |
| 2 | `reserva` no llevaba recomendador: nadie comprobaba el aforo del espacio pedido ("bloquear el Mirador para 300"). |
| 3 | `cambio_reserva`, `queja` y `persona` escalan y necesitan el contacto, pero consentimiento no estaba en su fila. |
| 4 | `persona` junto a otra intención salía con ruta `incidencia` si no se pasaba el tema. |
| 5 | Queja + evento nuevo llevaba a tres preguntas en un mensaje, sin orden definido. |

## Cambio (decidido por el equipo)

| # | Decisión | Dónde |
|---|---|---|
| 1 | Campo `rutas_adicionales` en el contrato ("lista con las rutas de las demás intenciones del mensaje; el dashboard cuenta un lead si lead aparece en ruta o en rutas_adicionales"). `router.py` lo devuelve. | `KNOWLEDGE.md` §3, `router.py` |
| 2 | Fila `reserva`: "Cualificador (condiciones del bloqueo) + recomendador (valida el espacio elegido) + consentimiento". En §3: "Si el recomendador descarta el espacio elegido (aforo, antelación u horario), se explica el motivo y se proponen las alternativas que dé el script." | Skill §2 y §3, `router.py` |
| 3 | "+ consentimiento para el contacto" en `cambio_reserva`, `queja` y `persona`. | Skill §2, `router.py` |
| 4 | "Si persona va con otra intención, la ruta del tema es la de esa otra intención." | Skill §4, `router.py` |
| 5 | "Con una queja y un evento nuevo: primero se reconoce la queja (quién responde y en qué plazo) y se hace una sola pregunta del evento. El contacto se pide una sola vez, en el mensaje siguiente, y sirve para los dos temas." | Skill §4 |

Además, en esta ronda se actualizó en `KNOWLEDGE.md` la línea de "LLMs vs. modelos de decisión" (§2), para que siga la nueva regla 3.

## Después

- `scripts/test_router.py`: **12/12**. Los 9 de antes no cambiaron; los 3 nuevos son queja + nuevo_evento → `rutas_adicionales` [lead], persona + nuevo_evento → ruta `lead`, y reserva → incluye recomendador.
- Prueba 02:
  - Las dos frases con varias intenciones cumplen: el lead queda en `rutas_adicionales`, y en la queja el contacto se pide una sola vez para los dos temas.
  - "Bloquear el Mirador para 300" cumplió **en parte** en la primera pasada. La respuesta explicaba el descarte y proponía la Nau, pero el motivo (aforo) no lo daba el script: `recomendar.py` solo devolvía los descartes por antelación u horario.

## Ronda 2: validación del espacio elegido

- **Problema:** la regla nueva de §3 pedía explicar por qué se descarta el espacio elegido, y el script no daba el motivo cuando era el aforo.
- **Cambio (decidido por el equipo):**
  - `recomendar.py` tiene una opción nueva, `validar_espacio` (`--validar ID`). Recibe espacio, asistentes, disposición y, si se conocen, días y hora de fin.
  - Devuelve si encaja y, si no, todos los motivos (aforo de esa disposición, antelación, horario) con el dato que falla, más las alternativas de la recomendación normal.
  - En la skill del router (§3), "Si el recomendador descarta el espacio elegido" pasa a ser "Si la validación del script descarta el espacio elegido".
- **Tests nuevos en `test_recomendar.py`:**
  - Mirador, 300 en cóctel, 14 de marzo → no encaja (aforo en cóctel: 210); alternativa, la Nau.
  - Mirador, 100 en banquete → encaja.
  - Nau, 180 en teatro, dentro de 5 días → no encaja (necesita 14 días).
  
  Resultado: **24/24** (los 21 de antes siguen pasando). Router 12/12.
- **Después:** el caso 1b de la prueba 02 cumple. El chatbot pregunta el formato, valida con el script y explica el motivo con su dato ("en cóctel caben 210"). La alternativa que propone (la Nau) es la que da el script.
- **Queda abierto:** la skill del router no dice de forma explícita que, en `reserva`, se pregunte la disposición antes de validar. En la prueba se hizo así porque el recomendador la pide como dato obligatorio.
