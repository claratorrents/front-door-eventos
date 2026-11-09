---
name: recomendador-espacios
description: Recomienda de 1 a 3 espacios del catálogo según tipo de evento, asistentes, disposición, fecha y hora de fin, y los presenta en tarjetas sin precio. Úsala cuando el cliente quiere organizar un evento y ya se conoce, al menos, el número de asistentes y el tipo de evento o la disposición. La elección y el orden los decide scripts/recomendar.py; el LLM solo redacta. Si el cliente elige un espacio, su nombre va en preferred_location del envío a n8n. No se usa para dar precios, confirmar disponibilidad ni puntuar el lead.
---

# Recomendador de espacios

Se aplica junto con guardrails, cualificador-leads y media-espacios. Datos en `${CLAUDE_SKILL_DIR}/../../data/espacios.json`; contexto en `${CLAUDE_SKILL_DIR}/../../KNOWLEDGE.md` §3.1 y §3.2.

## 1. Qué necesita
- **Obligatorio:** número de asistentes y disposición.
- **Disposición:** si el cliente no la dice, se deduce del tipo de evento y se confirma en la misma frase ("Para una conferencia lo normal es formato teatro; ¿os encaja?"):
  - conferencia, presentación, lanzamiento → `theater`
  - cena, comida, boda → `banquet`
  - networking, cóctel, fiesta → `cocktail`
  - formación, taller, curso → `classroom`
  Se recomienda en ese mismo mensaje para no hacer esperar al cliente. Si después dice que la disposición no es esa, se vuelve a ejecutar el script con la nueva.
- **Opcional:** fecha del evento (para la antelación) y hora de fin (para el horario).
- Si el tipo de evento suele acabar tarde (fiesta, cena, cena de gala, boda) y no dice la hora: se pregunta "¿Hasta qué hora más o menos?" antes de recomendar.
- **Hora ambigua** ("hasta las 9"): se pregunta "¿Las 9 de la noche?". De 1 a 7 sin más contexto se entiende madrugada. De 8 a 12 sin 'de la mañana' o 'de la noche', se pregunta. Al script siempre se le pasa la hora en formato 24 h (21:00).
- Si falta lo obligatorio, se pregunta (una o dos preguntas por mensaje, contando las del cualificador; router §3) y no se recomienda todavía.
- **Día exacto más tarde:** si el cliente ya eligió espacio y después da el día exacto, se vuelve a validar ese espacio con `${CLAUDE_SKILL_DIR}/../../scripts/recomendar.py --validar` (antelación). Si ya no encaja, se explica el motivo y se proponen las alternativas que dé el script.

## 2. La decisión la toma el script
Se ejecuta `${CLAUDE_SKILL_DIR}/../../scripts/recomendar.py` con asistentes, disposición y, si se conocen, días hasta el evento y hora de fin, y la zona, si el cliente la ha dicho (--zona). El script aplica estas reglas, en este orden:
1. **Aforo:** se usa el de la disposición pedida, nunca `absolute_max`. Fuera todo espacio con menos aforo que asistentes.
2. **Antelación:** si se sabe la fecha, fuera los espacios cuyo `min_lead_time_days` no se cumple.
3. **Horario:** si se sabe la hora de fin, fuera los espacios cuya `max_end_time` es anterior.
4. **Ocupación** = asistentes / aforo de la disposición:
   - del 60 % al 90 % → `comodo`
   - más del 90 % → `al_limite`
   - menos del 60 % → `bajo_60`: solo se recomienda si no queda ningún espacio `comodo` ni `al_limite`.
   - Si la única opción es al_limite, se añade como alternativa el primer espacio bajo_60.
5. **Orden:** primero `comodo`, después `al_limite`, después `bajo_60`. Dentro de cada grupo, la ocupación más cercana al 80 %. **Empate:** primero el espacio con menos aforo en esa disposición.
6. **Máximo 3** espacios.
7. **Descartados:** el script devuelve también los espacios descartados por antelación u horario y el motivo, para poder explicarlo.

El LLM nunca cambia el orden ni añade espacios que el script no devuelve. **El porcentaje de ocupación es un dato interno: nunca se enseña al cliente.**

## 3. Cómo se presenta (tarjeta por espacio)
- **Nombre** y **tagline**.
- **Aforo en esa disposición** ("hasta 150 personas en banquete").
- **Por qué encaja:** una frase usando `best_for`, **solo si** el tipo de evento está en `event_types`. Si no aparece, la frase se limita al dato: "Tiene sitio para 160 personas en formato teatro." Nunca se inventa.
- La frase de 'por qué encaja' usa el tipo de evento de event_types, nunca copia literalmente best_for.
- Usa el artículo correcto con cada nombre (el Jardí, la Nau).
- **Una foto aprobada** (`approved: true`) que encaje con el evento (cena → foto de banquete); si no hay una que encaje, la primera foto aprobada. Nunca la ruta del archivo.
- Horarios por zona: si el script devuelve avisos_zona para un
  espacio, la tarjeta lo dice siempre. Ejemplo, Mirador: 'El salón
  hasta las 03:00; la terraza cierra a las 23:30.' El LLM no deduce
  horarios por zona por su cuenta: solo redacta lo que da el script.
- Si es `al_limite`:
  - con otra opción delante: "Cabe justo; si podéis ser alguno más, mejor [primera opción]."
  - si es la única opción y el script da una alternativa: 'Cabe justo. Si preferís más margen, el [alternativa] tiene sitio para [N]; os quedaría holgado.'
  - si no hay ninguna alternativa: 'Cabe justo; si al final sois alguno más, avísanos y buscamos otra opción.'
- Si es `bajo_60` (porque no hay otra opción): "Es más grande de lo que necesitáis, pero es el que encaja con [horario / fecha]."
- Si el espacio elegido queda en bajo_60, se respeta la elección y se avisa: 'Os quedará amplio. Si preferís algo más ajustado, [espacio] tiene sitio para [N].', solo si la respuesta de `${CLAUDE_SKILL_DIR}/../../scripts/recomendar.py --validar` trae una opción comodo (`opcion_comodo`).
- **Nunca precio** (guardrails, regla 1). Nunca "está disponible" (guardrails, regla 2).
- Si el cliente ha dicho una zona, primero los espacios de esa zona. Los de otras zonas se presentan aparte: 'Fuera de [zona], también os encajaría…'. Si en su zona no encaja ninguno: 'En [zona] no tenemos ningún espacio que encaje; os propongo estos en otras zonas.'
- Si en su zona solo hay un espacio que queda muy amplio (bajo_60): 'En [zona] tenemos [espacio], aunque para [n] personas os quedaría muy amplio. Fuera de [zona], os encajaría mejor…' y se presenta la mejor opción comodo de otra zona.
- Al final, una sola pregunta que junta las dos: "¿Cuál os encaja más? También puedo enseñaros el plano o más fotos."
- **Elección:** el espacio que elija el cliente va en `preferred_location` del envío (KNOWLEDGE §3.2, decisión 2), y desde ese momento se puede decir el nombre de su comercial (guardrails, "Nombre del comercial").

## 4. Descartes que hay que explicar
- Por antelación: "Para esa fecha, la Nau del Besòs no llega: necesita 14 días de preparación."
- Por horario: "El Fòrum de les Corts no encaja: el horario acaba a las 22:00."
- **Jardí de Gràcia por horario:** "En el Jardí la música en el patio acaba a las 22:30; el horario en el interior lo confirmará el comercial cuando te contacte." Si el cliente quiere el Jardí igualmente, se apunta para el message ("Pregunta por el horario interior del Jardí"). (Se descarta con el dato que sí tenemos: mejor perder una opción que prometer lo que no sabemos.)
- Por aforo no hace falta explicar cada espacio descartado.

## 5. Si no queda ningún espacio
- **Por aforo** (ninguno es lo bastante grande): "Ninguno de nuestros espacios tiene sitio para [N] personas en [disposición]. Si quieres, sigo con tu consulta y la paso al equipo para que vea qué opciones hay." → al message: "Ningún espacio tiene aforo para [N] en [disposición]".
- **Por antelación** (no llegan a tiempo): "Para esa fecha no llegamos a preparar ningún espacio que encaje. Si quieres, sigo con tu consulta y la paso al equipo para que vea si hay alguna opción." → al message: "Fecha con menos antelación de la necesaria".
- En los dos casos la consulta sigue su camino normal (cualificador, consentimiento y envío a n8n; n8n la pasa al equipo de eventos). Sin nombre de comercial y sin plazos (KNOWLEDGE §3.2, decisiones 7 y 9). → `escalar_comercial`, motivo `excepcion`, en los dos casos.

## 6. Más detalles
- Si el cliente pide más información de un espacio: `full_profile` y, si los pide, plano o fotos aprobados.
- Políticas del espacio (catering, parking, horario): solo con los datos del espacio (guardrails, regla 7).

## 7. Ejemplos
- Cliente: "Cena de empresa para 120 personas en marzo."
  Antes de recomendar: "¿Hasta qué hora más o menos?" Cliente: "Hasta las 00:00." El resultado del script no cambia.
  Script: Llum del Poblenou (`comodo`), Mirador de Montjuïc (`al_limite`).
  Bien: tarjeta de Llum ("hasta 150 en banquete; pensado para cenas") y tarjeta del Mirador con "Cabe justo; si podéis ser alguno más, mejor Llum".
  Mal: recomendar la Nau del Besòs: se vería medio vacía. Mal: "Llum, ocupación 80 %".
- Cliente: "Fiesta para 100 personas hasta las 3."
  Script: Mirador y Nau, ambos `bajo_60`, porque el horario descarta los demás.
  Bien: explicar que son grandes pero encajan con el horario, que el Mirador tiene la terraza hasta las 23:30, que Llum acaba a las 02:00 y lo del Jardí.
- Cliente: "Comida para 33 personas."
  Script: Atelier (`al_limite`) y Jardí de Gràcia (`bajo_60`) como alternativa.
  Bien: "Cabe justo. Si preferís más margen, el Jardí de Gràcia tiene sitio para 60; os quedaría holgado."
- Cliente: "Conferencia para 180 personas dentro de 5 días."
  Script: ninguno (Llum necesita 7 días y la Nau 14).
  Bien: explicar la antelación y ofrecer seguir con la consulta para pasarla al equipo (al message: "Fecha con menos antelación de la necesaria"; `escalar_comercial`, `excepcion`).
