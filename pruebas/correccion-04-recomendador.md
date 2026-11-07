# Corrección 04 · Recomendador de espacios

Fecha: 7 de noviembre de 2026
Archivos: `.claude/skills/recomendador-espacios/SKILL.md`, `scripts/recomendar.py`, `scripts/test_recomendar.py`, `data/espacios.json` (`max_end_time`), `scripts/validar_datos.py`
Pruebas: `pruebas/prueba-recomendador-01.md` (antes) y `pruebas/prueba-recomendador-02.md` (después)

## Antes

Primera versión de la skill, escrita por el equipo, con la decisión en `scripts/recomendar.py`. El script pasó los 8 casos calculados por el equipo (8/8) y las 4 frases de la prueba 01 cumplieron. Leídas como cliente y comparadas con guardrails, salieron estos problemas.

## Problema

| # | Qué falló o no convencía en la prueba 01 |
|---|---|
| 1 | Jardí: el recomendador lo descartaba "porque la música acaba a las 22:30", mientras guardrails trata el horario interior como "sin dato". Las dos skills decían cosas distintas. |
| 2 | Mirador: `max_end_time` 03:00 es el del salón; la terraza cierra a las 23:30 y la tarjeta no lo decía. |
| 3 | Un único espacio `al_limite` (33 en banquete → Atelier): la frase "si podéis ser alguno más, mejor [primera opción]" no tenía primera opción. |
| 4 | "Si no queda ningún espacio": no decía cuándo responde David Ramos, y el motivo `lead` no encajaba con la falta de antelación, que guardrails trata como `excepcion`. |
| 5 | "Por qué encaja" cuando `best_for` no menciona el evento: el LLM estiraba la frase (Mirador para una conferencia). |
| 6 | Empates a la misma distancia del 80 %: el orden dependía del orden del JSON. |
| 7 | Horas ambiguas: "hasta las 9" se habría leído como las 09:00. |
| 8 | Se recomendaba antes de que el cliente confirmara la disposición, sin decir qué pasa si la cambia. |
| 9 | La ocupación (%) podía acabar en la respuesta al cliente. |

## Cambio (decidido por el equipo)

| # | Decisión | Dónde |
|---|---|---|
| 1 | Jardí: se descarta con el dato que sí hay, con frase propia: "En el Jardí la música en el patio acaba a las 22:30; el horario en el interior lo confirma el equipo." Mejor perder una opción que prometer lo que no se sabe. | Skill §4 |
| 2 | Si hay horarios distintos por zona y el evento pasa del más temprano, la tarjeta lo dice ("El salón hasta las 03:00; la terraza cierra a las 23:30"). | Skill §3 |
| 3 | Frase nueva para cuando es la única opción: "Cabe justo; si al final sois alguno más, avísanos y buscamos otra opción." | Skill §3 y §7 |
| 4 | Dos casos: sin aforo → `lead`; sin antelación → `excepcion`. Los dos con David Ramos y "te responde en 24 h laborables". | Skill §5 y §7 |
| 5 | "Por qué encaja" solo si el tipo de evento aparece en `best_for`; si no, solo el dato ("Tiene sitio para 160 personas en formato teatro"). Nunca se inventa. | Skill §3 |
| 6 | Empate: primero el espacio con menos aforo en esa disposición. En el script se compara con fracciones exactas (con decimales, 70 % y 90 % no salían empatados) y hay un test con datos de prueba en los dos órdenes del JSON. | Skill §2, `recomendar.py`, `test_recomendar.py` |
| 7 | Hora ambigua: se pregunta "¿Las 9 de la noche?"; al script siempre se le pasa en formato 24 h. | Skill §1 |
| 8 | Se recomienda en el mismo mensaje; si el cliente cambia la disposición, se vuelve a ejecutar el script. | Skill §1 |
| 9 | La ocupación es un dato interno y nunca se enseña al cliente. Los ejemplos ya no la muestran, y hay un ejemplo "Mal" nuevo ("Llum, ocupación 80 %"). | Skill §2 y §7 |

## Después

- `scripts/test_recomendar.py`: 9/9 (los 8 casos del equipo, que siguen igual, y el desempate).
- Prueba 02: las 6 frases cumplen (las 4 de antes, "Cena para 33 personas" y "Fiesta para 100 personas hasta las 9").
- Quedan abiertos, sin hacer fallar la prueba:
  - Qué cuenta como "aparece en `best_for`" lo decide el LLM.
  - Una cena en el Atelier puede pasar de su cierre a las 21:00 sin que se pregunte la hora.
  - Con un único espacio `al_limite`, los `bajo_60` cercanos al 60 % no se ofrecen como alternativa.
  - No está definido qué horas son ambiguas.

---

## Ronda 3: event_types y alternativa

### Problema (puntos abiertos tras la prueba 02)
- Qué cuenta como "el tipo de evento aparece en `best_for`" lo decidía el LLM.
- Una cena podía pasar del cierre de un espacio (Atelier, 21:00) sin que se preguntara la hora.
- Con un único espacio `al_limite`, no se ofrecía ninguna alternativa (fiesta de 100 hasta las 21:00 → solo el Jardí).
- No estaba definido qué horas son ambiguas.

### Cambio (decidido por el equipo)
- Nuevo campo `event_types` en cada espacio (Llum: presentacion, conferencia, cena, hackathon · Jardí: reunion, networking, presentacion, taller · Mirador: cena, gala, reunion, networking · Atelier: taller, reunion, formacion · Fòrum: formacion, conferencia, asamblea · Nau: conferencia, feria, rodaje, cena). El validador lo exige. "Por qué encaja" solo si el tipo de evento está en `event_types`.
- "Cena" pasa a la lista de eventos que suelen acabar tarde: se pregunta la hora antes de recomendar.
- Horas ambiguas: de 1 a 7 sin más contexto, madrugada; de 8 a 12 sin "de la mañana" o "de la noche", se pregunta.
- Regla 4: si la única opción es `al_limite`, se añade como alternativa el primer `bajo_60`. El script lo aplica y marca `alternativa: true`.
- Frases de §3: única opción con alternativa ("Cabe justo. Si preferís más margen, el [alternativa] tiene sitio para [N]; os quedaría holgado.") y sin alternativa ("Cabe justo; si al final sois alguno más, avísanos y buscamos otra opción.").
- Ejemplos de §7: la cena de 120 pregunta la hora antes de recomendar; "Cena para 33" pasa a "Comida para 33" con el Jardí como alternativa.
- Test: el caso de 33 en banquete pasa a esperar Atelier + Jardí (decidido por el equipo), y hay un caso nuevo para la fiesta de 100 hasta las 21:00 (Jardí + Fòrum).

### Después
- `scripts/test_recomendar.py`: 10/10. Validador: todo correcto.
- Prueba 03 (`pruebas/prueba-recomendador-03.md`): las 4 frases cumplen.
- Al redactar la prueba 03 se me olvidó primero el horario por zonas del Mirador en la cena de 120 hasta las 00:00. Lo corregí al revisar: el script no avisa de los horarios por zona, así que depende de la redacción.
- Quedan abiertos, sin hacer fallar la prueba:
  - Cuando un espacio es `bajo_60`, `best_for` puede sonar raro ("Cenas de empresa masivas" para 33 personas).
  - El artículo de "el [alternativa]".
