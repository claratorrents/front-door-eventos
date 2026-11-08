# Corrección 12 · Recomendador de espacios

Fecha: 8 de noviembre de 2026
Archivos:
- `.claude/skills/recomendador-espacios/SKILL.md`: md5 `0858a9d9102fbf7d72b5b726d7db9029` → `838289137819ee507535d2ebd77a9072`. La versión nueva la escribió el equipo.
- `scripts/recomendar.py` y `scripts/test_recomendar.py`.

Motivo: integración con el flujo de n8n de Ale (`KNOWLEDGE.md` §3.2, decisiones 2, 6, 7 y 9), más lo que quedó abierto en el router (corrección 10: `--validar` sin `avisos_zona`). Punto 6 del paso 2 de la integración.
Pruebas: `pruebas/prueba-recomendador-03.md` (antes) y `pruebas/prueba-recomendador-04.md` (después).

## Antes

- **Sin espacio que encaje:** "Paso tu consulta a David Ramos… en 24 h laborables", con `escalar_comercial` y motivo `lead` (por aforo) o `excepcion` (por antelación), y se pedía el contacto.
- **Jardí por horario:** "el horario en el interior lo confirma el equipo".
- **Pregunta final:** solo "¿Queréis ver el plano o el recorrido 360°…?". El cualificador pedía además "¿Cuál os encaja más?".
- **Día exacto tardío:** nada decía qué pasaba si el cliente daba el día después de elegir espacio.
- **`--validar`:** no devolvía `avisos_zona`.

## Problema

| # | Qué choca | Dónde |
|---|---|---|
| 1 | Sin espacio que encaje, la consulta sigue y se envía a n8n. No hay comercial que nombrar (decisión 9), ni plazos ni petición de contacto aparte (decisión 7). El motivo `lead` ya no existe | §3.2 |
| 2 | Lo que no se resuelve dentro de una consulta va al `message` | §3.2, decisión 6 |
| 3 | El espacio elegido tiene que viajar en `preferred_location` | §3.2, decisión 2 |
| 4 | Dos preguntas finales que competían (recomendador y cualificador) | Prueba cualificador 03 |
| 5 | La tarjeta de un espacio elegido no podía mostrar el aviso de zona sin que el LLM lo dedujera | Prueba router 03 |

## Cambio

**Skill (texto del equipo):**
- **§1:** las preguntas se cuentan junto con las del cualificador (router §3). Si el cliente da el día exacto después de elegir, se vuelve a validar el espacio con `--validar`.
- **§3:** una sola pregunta final: "¿Cuál os encaja más? También puedo enseñaros el plano o el recorrido 360°." El espacio elegido va en `preferred_location` y desde entonces se puede nombrar al comercial.
- **§4, Jardí:** "lo confirmará el comercial cuando te contacte". Si lo quiere igualmente, se apunta para el message.
- **§5:** sin espacio, por aforo o por antelación, se ofrece seguir con la consulta. Se apunta para el message, sin nombre ni plazos, con `escalar_comercial` y `excepcion` en los dos casos.
- **Descripción y §7:** ajustadas a lo anterior.

**Script (`recomendar.py`):**
- El cálculo de las zonas que cierran antes de la hora de fin pasa a una función, `avisos_de_zona`, que usan la recomendación normal y `--validar`.
- `--validar` devuelve siempre `avisos_zona`. La recomendación normal da el mismo resultado que antes.

**Test:** caso nuevo "validar: Mirador, 100 banquet, hasta las 01:00 → encaja, con aviso de la terraza (23:30)".

**Motivo `lead`:** comprobado que no queda en skills ni scripts.
- Guardrails solo lo nombra para decir que queda sustituido.
- En `router.py`, `lead` es una ruta, no un motivo.
- En `KNOWLEDGE.md` solo queda en la lista de `motivo_escalado` del contrato anterior, la sección que se conserva como referencia.

## Después

- `test_recomendar.py`: **25/25**. Los 24 anteriores siguen pasando y el nuevo también.
- Resto: `test_datos_consulta.py` 10/10, `test_router.py` 12/12, validador correcto.
- Prueba 04: **los 4 casos cumplen**.
  - **Cena para 120:** pregunta final nueva y `preferred_location`.
  - **500 en cóctel:** sin espacio, la consulta sigue y va al message.
  - **Mirador y luego día exacto:** se revalida. Con el 20 de noviembre encaja (12 días ≥ 10); con la variante del 15, no llega y se propone el Llum.
  - **Fiesta hasta la 1 en el Mirador:** el aviso de la terraza sale de `--validar`.

**Queda abierto** (comentarios de la prueba 04):
1. `--validar` no devuelve la foto de la tarjeta, que respeta la regla de las zonas con aviso. En la prueba la saqué con `foto_tarjeta`.
2. Espacio elegido `bajo_60` (por ejemplo, el Mirador para 100 en cóctel): no está dicho si se avisa al cliente.
3. El ejemplo de la §7 ("pensado para cenas de gala") copia `best_for`, y la §3 lo prohíbe.
4. En `KNOWLEDGE.md`, la lista de `motivo_escalado` del contrato anterior sigue con `lead`, y la de `decision` con `consulta_disponibilidad` y `prerreserva`. El registro anónimo (decisión 11) se basa en esa sección.
