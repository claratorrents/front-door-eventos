# Prueba recomendador 03

Fecha: 7 de noviembre de 2026
Skill: `.claude/skills/recomendador-espacios/SKILL.md`, versión 2, con los cambios de esta ronda: `event_types`, "cena" entre los eventos que suelen acabar tarde, horas ambiguas, alternativa `bajo_60` y frases nuevas de §3 y §7.
Script: `scripts/recomendar.py` con la regla de la alternativa (campo `alternativa`). `scripts/test_recomendar.py`: **10/10**.
Datos: `data/espacios.json` con `event_types`; el validador da "todo correcto".
Método: igual que las pruebas 01 y 02. **[aviso de IA]** abrevia el aviso del primer mensaje. La ocupación solo aparece en la línea "Script" (dato interno).

## 1. "Cena de empresa para 120 personas en marzo"

- **Primera respuesta** (cena → se pregunta la hora antes de recomendar):
  > [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? ¿Y hasta qué hora más o menos?
- **Continuación** (C: "Sí, hasta las 00:00"). Script `120 banquet --hora-fin 00:00` → Llum del Poblenou (80 %, `comodo`), Mirador de Montjuïc (100 %, `al_limite`). Sin descartes: el resultado no cambia respecto al caso sin hora.
  > **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Pensado para cenas de gala. *[foto: llum-poblenou-foto-01]*
  >
  > **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Pensado para cenas corporativas. El salón hasta las 03:00; la terraza cierra a las 23:30. Cabe justo; si podéis ser alguno más, mejor Llum del Poblenou. *[foto: mirador-montjuic-foto-02]*
  >
  > ¿Queréis ver el plano o el recorrido 360° de alguno?
- **decision:** ninguna · **¿Cumple?** Sí. Pregunta la hora antes de recomendar, como en el ejemplo nuevo de §7. "Cena" está en `event_types` de los dos espacios, así que el "por qué encaja" sale de `best_for`. La cena acaba a las 00:00, después de que cierre la terraza del Mirador (23:30), así que su tarjeta da el horario por zonas (§3).

## 2. "Comida para 33 personas"

- **Datos:** comida → `banquet`. "Comida" no está entre los eventos que suelen acabar tarde: no se pregunta la hora.
- **Script:** `33 banquet` → Atelier de Sant Antoni (94 %, `al_limite`) y Jardí de Gràcia (55 %, `bajo_60`, `alternativa: true`).
- **Respuesta:**
  > [aviso de IA] Para una comida lo normal es formato banquete; ¿os encaja? Tengo esta opción:
  >
  > **Atelier de Sant Antoni.** Estudio boutique diáfano para diseño, sprints y dinámicas ágiles. Tiene sitio para 35 personas en banquete. Cabe justo. Si preferís más margen, el Jardí de Gràcia tiene sitio para 60; os quedaría holgado. *[foto: atelier-sant-antoni-foto-01]*
- **decision:** ninguna · **¿Cumple?** Sí. Usa la frase nueva de "única opción con alternativa", con el aforo del Jardí en banquete (60). "Comida" no está en `event_types` del Atelier, así que solo da el dato. He quitado la pregunta final del plano para no pasar de dos preguntas.

## 3. "Fiesta para 100 personas hasta las 9"

- **Primera respuesta** (9 está entre 8 y 12 sin "de la mañana" ni "de la noche": se pregunta):
  > [aviso de IA] Para una fiesta lo normal es formato cóctel, de pie; ¿os encaja? ¿Las 9 de la noche?
- **Continuación** (C: "Sí, de la noche"). Script `100 cocktail --hora-fin 21:00` → Jardí de Gràcia (91 %, `al_limite`) y Fòrum de les Corts (59 %, `bajo_60`, `alternativa: true`).
  > **Jardí de Gràcia.** Oasis botánico y patio íntimo entre callejuelas históricas. Tiene sitio para 110 personas en formato cóctel. Cabe justo. Si preferís más margen, el Fòrum de les Corts tiene sitio para 170; os quedaría holgado. *[foto: jardi-gracia-foto-01]*
  >
  > ¿Queréis ver el plano o el recorrido 360°?
- **decision:** ninguna · **¿Cumple?** Sí. Aplica la regla de horas ambiguas y pasa la hora al script en formato 24 h. Ofrece el Fòrum como alternativa, que era el punto abierto de la prueba 02. "Fiesta" no está en `event_types`, así que solo da el dato.

## 4. "Cena para 33 personas hasta las 23:00"

- **Datos:** cena → `banquet`. La hora ya viene dada (23:00, sin ambigüedad), así que no se pregunta.
- **Script:** `33 banquet --hora-fin 23:00` → Mirador de Montjuïc (28 %), Llum del Poblenou (22 %) y Nau del Besòs (15 %), los tres `bajo_60`. Descartados por horario: Jardí (22:30), Atelier (21:00) y Fòrum (22:00).
- **Respuesta:**
  > [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? Hasta las 23:00, los espacios a vuestra medida cierran antes, así que estos son más grandes de lo que necesitáis:
  >
  > **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Pensado para cenas corporativas. Es más grande de lo que necesitáis, pero es el que encaja con el horario. *[foto: mirador-montjuic-foto-02]*
  >
  > **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Pensado para cenas de gala. Es más grande de lo que necesitáis, pero es el que encaja con el horario. *[foto: llum-poblenou-foto-01]*
  >
  > **Nau del Besòs.** Nave monumental de 800 m² para ferias, convenciones y montajes de gran formato. Hasta 220 personas en banquete. Pensado para cenas de empresa. Es más grande de lo que necesitáis, pero es el que encaja con el horario. *[foto: nau-besos-foto-02, cena con mesas redondas]*
  >
  > El Atelier de Sant Antoni no encaja: el horario acaba a las 21:00. El Fòrum de les Corts tampoco: acaba a las 22:00. En el Jardí la música en el patio acaba a las 22:30; el horario en el interior lo confirma el equipo.
- **decision:** ninguna · **¿Cumple?** Sí. Respeta el orden del script (máximo 3), explica los tres descartes por horario (el del Jardí con su frase propia) y usa la frase de `bajo_60`. La cena acaba a las 23:00, antes de que cierre la terraza del Mirador (23:30), así que no hace falta hablar del horario por zonas.

**Resultado:** las 4 frases cumplen. Tests: 10/10. Validador: todo correcto.

## Comentarios (no hacen fallar la prueba)

1. **Caso 1, corregido al revisar:** en el primer borrador se me olvidó el horario por zonas del Mirador (la cena acaba a las 00:00 y la terraza cierra a las 23:30). Era un fallo de redacción, no de la skill, y ya está corregido arriba. Muestra que es fácil saltarse esa regla: el script no avisa de los horarios por zona.
2. **Nau para 33 personas:** su `best_for` dice "Cenas de empresa masivas". Para 33 personas he escrito "Pensado para cenas de empresa" para no decir "masivas" a un grupo pequeño; eso ya es adaptar el dato. Quizá conviene que, cuando el espacio es `bajo_60`, la tarjeta no use `best_for`.
3. **Caso 4, tres espacios grandes y ninguno a medida:** es lo que dicen las reglas (todos los pequeños cierran antes de las 23:00). El mensaje es largo: tres tarjetas y tres descartes.
4. **Frase de alternativa con artículo:** "el [alternativa]" funciona con "el Jardí" y "el Fòrum". Con "la Nau" o "el Llum" habría que concordar el artículo; el LLM lo hará, pero la plantilla no lo prevé.
