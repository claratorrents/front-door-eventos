# Corrección 09 · Cualificador de leads

Fecha: 8 de noviembre de 2026
Archivos:
- `.claude/skills/cualificador-leads/SKILL.md`: md5 `fe00ea85d3ccef42a3fb6942d38dda70` → `ac285e4f7172446cfae8d702ad34a9ee`. La versión nueva la escribió el equipo.
- `scripts/puntuar_lead.py` y `scripts/test_puntuar_lead.py` (borrados) → `scripts/datos_consulta.py` y `scripts/test_datos_consulta.py`.
- Referencias en `KNOWLEDGE.md` (§7) y `scripts/empaquetar_plugin.py` (README del plugin).

Motivo: integración con el flujo de n8n de Ale (`KNOWLEDGE.md` §3.2, decisiones 3, 4 y 10). Punto 3 del paso 2 de la integración.
Pruebas: `pruebas/prueba-cualificador-02.md` (antes) y `pruebas/prueba-cualificador-03.md` (después).

## Antes

- **Qué hacía:** el cualificador puntuaba el lead de 0 a 100 con `puntuar_lead.py`. Usaba pesos fijos: fecha 25, asistentes 20, presupuesto 20, tipo 15, empresa 10 y urgencia 10.
- **Qué decidía con la puntuación:** con más de 70 puntos, día exacto, espacio elegido y antelación cumplida, ofrecía el bloqueo provisional de 72 h (`prerreserva`). Si no, pasaba al comercial (`escalar_comercial`, `lead`).
- **Qué recogía:** fecha, asistentes, presupuesto, tipo, empresa y urgencia.

## Problema

| # | Qué choca con la §3.2 | Decisión |
|---|---|---|
| 1 | La puntuación oficial es la de n8n. La del chat no se envía ni decide nada | 3 |
| 2 | No hay bloqueo de 72 h: el siguiente paso es la llamada por Calendly | 4 |
| 3 | El script del cualificador ya no puntúa: devuelve qué datos faltan | 10 |
| 4 | n8n necesita zona o espacio, fecha y presupuesto para asignar espacio, enviar el email automático y calificar bien el lead. Antes no se pedía la zona y sí la urgencia y la empresa, que el contrato no usa (la empresa la pide consentimiento) | Contrato |
| 5 | Los escalados dentro de una consulta (descuento, extras…) van en `message` | 6 |

## Cambio

**Skill (texto del equipo):**
- **§1:** para qué sirve: que la consulta llegue completa a n8n. No puntúa ni decide.
- **§2:** 7 datos en orden, con el campo del envío:
  - imprescindibles: tipo, asistentes, espacio o zona, y fecha (día, mes o temporada);
  - recomendables: día exacto, presupuesto y necesidades.
  - Ya no se piden urgencia ni empresa.
- **§3:** tabla de frases a niveles, más corta: fecha día, mes o temporada; asistentes y presupuesto "dado"; "no lo sabe".
- **§4:** el script devuelve qué falta, las siguientes preguntas (máximo dos) y `listo_para_enviar`. Cada dato se pregunta una sola vez.
- **§5:** los escalados dentro de una consulta se apuntan para `message`. Al cliente: "Lo verás con el comercial en la llamada."

**Script (`datos_consulta.py`, nuevo):** aplica la §2 y la §4 tal cual.
- **Entrada:** tipo, asistentes, espacio, zona, nivel de fecha (dia/mes/temporada/nada), presupuesto, necesidades y lista de datos ya preguntados.
- **Salida (JSON):** `datos_que_faltan`, `siguientes_preguntas` y `listo_para_enviar`.
- **Cómo lo interpreto:**
  - El espacio o la zona cuentan como el mismo dato.
  - El día exacto solo se pide si la fecha es mes o temporada.
  - "Faltan" son los datos que no están dados **ni** preguntados.
  - Las preguntas son las dos primeras de esa lista.
  - `listo_para_enviar` es verdadero cuando ya no falta ninguno.
- No lee datos ni la fecha del sistema: solo aplica el orden y las reglas.

**Borrados:** `puntuar_lead.py` y `test_puntuar_lead.py`. En `KNOWLEDGE.md` la mención histórica queda marcada como sustituida, y la línea de tests pasa a `test_datos_consulta.py`.

## Después

- `test_datos_consulta.py`: **10/10**.
  - Los 8 casos del equipo pasan sin ajustar ningún esperado.
  - Hay 2 casos más de entrada incorrecta: una fecha fuera de la lista y un dato preguntado desconocido dan error.
- Resto: `test_recomendar.py` 24/24, `test_router.py` 12/12, validador correcto.
- Prueba 03 (ruta estrella "Cena de empresa para 120 personas en marzo", hasta la pregunta de privacidad): **cumple**.
  - Preguntas del script, una o dos por mensaje.
  - El día exacto se pregunta una sola vez.
  - El descuento va a `message`.
  - Sin puntuación, sin bloqueo y sin precio.

**Queda abierto** (comentarios de la prueba 03):
1. Ninguna skill dice cómo se combinan las preguntas del recomendador (hora de fin) y las del cualificador. En la prueba, el recomendador fue primero.
2. La pregunta final de las tarjetas: "¿Cuál os encaja más?" (cualificador) frente a la única pregunta del recomendador (plano o 360°). Es para el punto 6.
3. La frase del descuento de guardrails ("te responden en 24 h laborables") choca con la §5. Es para el punto 5.
4. Sin día exacto no se comprueba la antelación.
5. **El plugin todavía lleva `puntuar_lead.py` y la skill antigua.** Se regenera en el punto 8.
