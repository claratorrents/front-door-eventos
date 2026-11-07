---
name: recomendador-espacios
description: Recomienda de 1 a 3 espacios del catálogo según tipo de evento, asistentes, disposición, fecha y hora de fin, y los presenta en tarjetas sin precio. Úsala cuando el cliente quiere organizar un evento y ya se conoce, al menos, el número de asistentes y el tipo de evento o la disposición. La elección y el orden los decide scripts/recomendar.py; el LLM solo redacta. No se usa para dar precios, confirmar disponibilidad ni puntuar el lead.
---

# Recomendador de espacios

Se aplica junto con guardrails y consentimiento. Datos en `data/espacios.json`; contexto en `KNOWLEDGE.md` §3.1.

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
- Si falta lo obligatorio, se pregunta (una o dos preguntas por mensaje) y no se recomienda todavía.

## 2. La decisión la toma el script
Se ejecuta `scripts/recomendar.py` con asistentes, disposición y, si se conocen, días hasta el evento y hora de fin. El script aplica estas reglas, en este orden:
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
- **Horarios por zona:** si el espacio tiene horarios distintos por zona (`noise_curfew`) y el evento pasa del más temprano, la tarjeta lo dice. Ejemplo, Mirador: "El salón hasta las 03:00; la terraza cierra a las 23:30."
- Si es `al_limite`:
  - con otra opción delante: "Cabe justo; si podéis ser alguno más, mejor [primera opción]."
  - si es la única opción y el script da una alternativa: 'Cabe justo. Si preferís más margen, el [alternativa] tiene sitio para [N]; os quedaría holgado.'
  - si no hay ninguna alternativa: 'Cabe justo; si al final sois alguno más, avísanos y buscamos otra opción.'
- Si es `bajo_60` (porque no hay otra opción): "Es más grande de lo que necesitáis, pero es el que encaja con [horario / fecha]."
- **Nunca precio** (guardrails, regla 1). Nunca "está disponible" (guardrails, regla 2).
- Al final, una sola pregunta para avanzar ("¿Queréis ver el plano o el recorrido 360° de alguno?").

## 4. Descartes que hay que explicar
- Por antelación: "Para esa fecha, la Nau del Besòs no llega: necesita 14 días de preparación."
- Por horario: "El Fòrum de les Corts no encaja: el horario acaba a las 22:00."
- **Jardí de Gràcia por horario:** "En el Jardí la música en el patio acaba a las 22:30; el horario en el interior lo confirma el equipo." (Se descarta con el dato que sí tenemos: mejor perder una opción que prometer lo que no sabemos.)
- Por aforo no hace falta explicar cada espacio descartado.

## 5. Si no queda ningún espacio
- **Por aforo** (ninguno es lo bastante grande): "Ninguno de nuestros espacios tiene sitio para [N] personas en [disposición]. Paso tu consulta a David Ramos, que lleva los eventos grandes; te responde en 24 h laborables." → `escalar_comercial`, motivo `lead`.
- **Por antelación** (no llegan a tiempo): "Para esa fecha no llegamos a preparar ningún espacio que encaje. Paso tu consulta a David Ramos para ver si hay alguna opción; te responde en 24 h laborables." → `escalar_comercial`, motivo `excepcion`.
- En los dos casos se pide el contacto (skill consentimiento).

## 6. Más detalles
- Si el cliente pide más información de un espacio: `full_profile` y, si los pide, plano o tour 360° aprobados.
- Políticas del espacio (catering, parking, horario): solo con los datos del espacio (guardrails, regla 7).

## 7. Ejemplos
- Cliente: "Cena de empresa para 120 personas en marzo."
  Antes de recomendar: "¿Hasta qué hora más o menos?" Cliente: "Hasta las 00:00." El resultado del script no cambia.
  Script: Llum del Poblenou (`comodo`), Mirador de Montjuïc (`al_limite`).
  Bien: tarjeta de Llum ("hasta 150 en banquete; pensado para cenas de gala") y tarjeta del Mirador con "Cabe justo; si podéis ser alguno más, mejor Llum".
  Mal: recomendar la Nau del Besòs: se vería medio vacía. Mal: "Llum, ocupación 80 %".
- Cliente: "Fiesta para 100 personas hasta las 3."
  Script: Mirador y Nau, ambos `bajo_60`, porque el horario descarta los demás.
  Bien: explicar que son grandes pero encajan con el horario, que el Mirador tiene la terraza hasta las 23:30, que Llum acaba a las 02:00 y lo del Jardí.
- Cliente: "Comida para 33 personas."
  Script: Atelier (`al_limite`) y Jardí de Gràcia (`bajo_60`) como alternativa.
  Bien: "Cabe justo. Si preferís más margen, el Jardí de Gràcia tiene sitio para 60; os quedaría holgado."
- Cliente: "Conferencia para 180 personas dentro de 5 días."
  Script: ninguno (Llum necesita 7 días y la Nau 14).
  Bien: explicar la antelación y pasar a David Ramos en 24 h laborables (`escalar_comercial`, `excepcion`).
