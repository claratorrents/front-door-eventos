# Prueba recomendador 01

Fecha: 7 de noviembre de 2026
Skill: `.claude/skills/recomendador-espacios/SKILL.md` (versión del equipo, md5 `9449055e3230830a76a367de8fa49944`, comprobado), junto con guardrails y consentimiento.
Script: `scripts/recomendar.py`. Test automático: `scripts/test_recomendar.py`, que pasa los 8 casos calculados por el equipo (8/8).
Método: Claude Code responde como el chatbot. Cada frase es el primer mensaje de la conversación, así que empieza con el aviso de IA (lo abrevio como **[aviso de IA]**). Las fotos se indican con su id: el chat web las mostrará como imagen, nunca con la ruta.

## 1. "Cena de empresa para 120 personas en marzo"

- **Datos:** 120 asistentes. Cena → `banquet`. "En marzo", sin día: no se puede calcular la antelación. Una cena de empresa no es "cena de gala", así que no se pregunta la hora.
- **Script:** `--asistentes 120 --disposicion banquet` → Llum del Poblenou 80 % `comodo`, Mirador de Montjuïc 100 % `al_limite`. Ningún descarte.
- **Respuesta:**
  > [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? Estas son las opciones:
  >
  > **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Encaja porque está pensada para cenas de gala. *[foto: llum-poblenou-foto-01, nave montada para cena de gala]*
  >
  > **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Encaja para cenas corporativas. Cabe justo; si podéis ser alguno más, mejor Llum del Poblenou. *[foto: mirador-montjuic-foto-02, salón en montaje banquete]*
  >
  > ¿Queréis ver el plano o el recorrido 360° de alguno?
- **decision:** ninguna · **¿Cumple?** Sí. Respeta el orden del script, no da precio ni disponibilidad, elige las fotos según el evento y no recomienda la Nau (55 %).

## 2. "Queremos una conferencia para 150"

- **Datos:** 150 asistentes. Conferencia → `theater`. Sin fecha ni hora.
- **Script:** `--asistentes 150 --disposicion theater` → Llum del Poblenou 75 % `comodo`, Mirador de Montjuïc 94 % `al_limite`.
- **Respuesta:**
  > [aviso de IA] Para una conferencia lo normal es formato teatro; ¿os encaja? Os propongo:
  >
  > **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 200 personas en teatro. Encaja porque se usa para lanzamientos de producto y jornadas de innovación. *[foto: llum-poblenou-foto-02, montaje de teatro frente a la pantalla]*
  >
  > **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 160 personas en teatro. Encaja para eventos C-Level y entregas de premios. Cabe justo; si podéis ser alguno más, mejor Llum del Poblenou. *[foto: mirador-montjuic-foto-01, terraza con vistas al puerto]*
  >
  > ¿Queréis ver el plano o el recorrido 360° de alguno?
- **decision:** ninguna · **¿Cumple?** Sí, aunque el "por qué encaja" del Mirador es flojo: su `best_for` no menciona conferencias (ver comentario 5). El Mirador no tiene foto en teatro, así que sale la primera aprobada, como dice la skill.

## 3. "Fiesta para 100 personas"

- **Datos:** 100 asistentes. Fiesta → `cocktail`. Es un evento que suele acabar tarde y no dice la hora, así que **se pregunta antes de recomendar**. Todavía no se ejecuta el script.
- **Respuesta:**
  > [aviso de IA] Para una fiesta lo normal es formato cóctel, de pie; ¿os encaja? ¿Y hasta qué hora más o menos?
- **decision:** ninguna · **¿Cumple?** Sí. Pregunta la hora y no recomienda todavía; son dos preguntas, el máximo permitido.
- **Continuación** (C: "Sí, cóctel, hasta las 3"). Script `--asistentes 100 --disposicion cocktail --hora-fin 03:00` → Mirador 48 % `bajo_60`, Nau 25 % `bajo_60`. Descartados por horario: Llum (02:00), Jardí (22:30) y Fòrum (22:00).
  > Hasta las 3 de la madrugada solo encajan dos espacios, y los dos son más grandes de lo que necesitáis:
  >
  > **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 210 personas en cóctel. Es más grande de lo que necesitáis, pero es el que encaja con el horario. La terraza cierra a las 23:30; el salón interior, a las 03:00. *[foto: mirador-montjuic-foto-01]*
  >
  > **Nau del Besòs.** Nave monumental de 800 m² para ferias, convenciones y montajes de gran formato. Hasta 400 personas en cóctel. Es más grande de lo que necesitáis, pero es el que encaja con el horario. *[foto: nau-besos-foto-01, escenario e iluminación]*
  >
  > Llum del Poblenou acaba a las 02:00, y el Jardí de Gràcia y el Fòrum de les Corts antes de medianoche. ¿Queréis ver el recorrido 360° de alguno?
- **decision:** ninguna · **¿Cumple?** Sí. Explica los descartes por horario y que son grandes. He añadido el horario de la terraza del Mirador por la regla 7 de guardrails (ver comentario 3).

## 4. "Conferencia para 180 personas dentro de 5 días"

- **Datos:** 180 asistentes. Conferencia → `theater`. Faltan 5 días.
- **Script:** `--asistentes 180 --disposicion theater --dias 5` → ninguno. Descartados por antelación: Llum (necesita 7 días) y Nau (14). Sin la fecha, Llum (90 %) y Nau (60 %) serían los dos `comodo`.
- **Respuesta:**
  > [aviso de IA] Para una conferencia lo normal es formato teatro. Para 180 personas en 5 días, ninguno de nuestros espacios llega a tiempo: Llum del Poblenou necesita 7 días de preparación y la Nau del Besòs, 14. Paso tu consulta a David Ramos, que lleva los eventos grandes, para ver qué opciones hay; te responde en 24 h laborables. Para que pueda contactarte necesito tu nombre y un email o teléfono. ¿Me das permiso para guardarlos solo para responder a esta consulta?
- **decision:** escalar_comercial · **motivo:** lead · **¿Cumple?** Sí. He añadido el plazo ("24 h laborables") porque guardrails obliga a decir quién y cuándo, y la frase de la skill (§5) no lo dice (ver comentario 2).

**Resultado:** las 4 frases cumplen (más la continuación de la 3). El script pasa los 8 casos del equipo.

## Comentarios

1. **Un solo espacio `al_limite`:** con 33 en banquete el script devuelve solo el Atelier (94 %). La frase "Cabe justo; si podéis ser alguno más, mejor [primera opción]" no tiene primera opción, y el Jardí (55 %) queda fuera aunque sería la alternativa si vienen más.
2. **§5 "Si no queda ningún espacio"** no dice cuándo responde David Ramos (guardrails lo exige). Además, en el caso 4 el problema es la antelación, y guardrails clasifica eso como excepción (`excepcion`), mientras la skill usa `lead`. Los dos motivos tienen sentido; conviene elegir uno.
3. **`max_end_time` y los horarios con matices:**
   - **Mirador:** 03:00 es el salón; la terraza cierra a las 23:30, y el script no lo distingue.
   - **Jardí:** 22:30 es solo la música en exterior. En guardrails, el horario interior es "sin dato" (`pendiente_confirmar`), pero el recomendador lo descarta como si acabara a las 22:30. Las dos skills dicen cosas distintas sobre el mismo espacio.
4. **Redondeo:** el grupo se calcula con la ocupación exacta y se muestra redondeada. Un 90,4 % se vería como "90 %" pero sería `al_limite`. Con los datos actuales no pasa en ningún caso probado.
5. **"Por qué encaja" cuando `best_for` no menciona el evento** (Mirador para una conferencia): el LLM tiene que estirar la frase. Riesgo pequeño de inventar; quizá conviene una regla tipo "si no hay `best_for` que encaje, no se justifica".
6. **Empates:** si dos espacios están a la misma distancia del 80 %, el orden depende del orden del JSON. Con los datos actuales no pasa en los casos probados.
7. **Hora de fin a partir de las 08:00:** "hasta las 9" se lee como 09:00 del mismo día (por la mañana), no como 21:00. El chatbot tendrá que pasar la hora en formato 24 h ("21:00").
8. **Disposición confirmada y recomendación en el mismo mensaje:** la skill recomienda antes de que el cliente confirme la disposición. Si dice que no ("mejor cóctel"), hay que volver a ejecutar el script.
