# Prueba recomendador 02

Fecha: 7 de noviembre de 2026
Skill: `.claude/skills/recomendador-espacios/SKILL.md` versión 2 (md5 `4be450bb1516217dacd6ff48c18a5987`, comprobado), junto con guardrails y consentimiento.
Script: `scripts/recomendar.py` con el desempate de la regla 5. `scripts/test_recomendar.py`: 9/9 (los 8 casos del equipo más el desempate con datos de prueba, en los dos órdenes del JSON).
Método: igual que la prueba 01. **[aviso de IA]** abrevia el aviso del primer mensaje. Las fotos se indican con su id; el chat las mostrará como imagen. El porcentaje de ocupación solo aparece en la línea "Script" (dato interno) y nunca en la respuesta.

## 1. "Cena de empresa para 120 personas en marzo"

- **Script:** `120 banquet` → Llum del Poblenou `comodo`, Mirador de Montjuïc `al_limite`.
- **Respuesta:**
  > [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? Estas son las opciones:
  >
  > **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Pensado para cenas de gala. *[foto: llum-poblenou-foto-01]*
  >
  > **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Pensado para cenas corporativas. Cabe justo; si podéis ser alguno más, mejor Llum del Poblenou. *[foto: mirador-montjuic-foto-02]*
  >
  > ¿Queréis ver el plano o el recorrido 360° de alguno?
- **decision:** ninguna · **¿Cumple?** Sí. No enseña porcentajes. El "por qué encaja" sale de `best_for` porque "cena" aparece en "Cenas de gala" y en "Cenas corporativas" (ver comentario 1). Como no se sabe la hora de fin, no hace falta hablar del horario por zonas.

## 2. "Queremos una conferencia para 150"

- **Script:** `150 theater` → Llum del Poblenou `comodo`, Mirador de Montjuïc `al_limite`.
- **Respuesta:**
  > [aviso de IA] Para una conferencia lo normal es formato teatro; ¿os encaja? Os propongo:
  >
  > **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Tiene sitio para 200 personas en formato teatro. *[foto: llum-poblenou-foto-02, montaje de teatro]*
  >
  > **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Tiene sitio para 160 personas en formato teatro. Cabe justo; si podéis ser alguno más, mejor Llum del Poblenou. *[foto: mirador-montjuic-foto-01]*
  >
  > ¿Queréis ver el plano o el recorrido 360° de alguno?
- **decision:** ninguna · **¿Cumple?** Sí. "Conferencia" no aparece en el `best_for` de ninguno de los dos, así que la tarjeta solo da el aforo. Ya no se estira la frase como en la prueba 01.

## 3. "Fiesta para 100 personas"

- **Primera respuesta** (sin script):
  > [aviso de IA] Para una fiesta lo normal es formato cóctel, de pie; ¿os encaja? ¿Y hasta qué hora más o menos?
- **Continuación** (C: "Sí, hasta las 3 de la madrugada"). Script `100 cocktail --hora-fin 03:00` → Mirador `bajo_60`, Nau `bajo_60`. Descartados por horario: Llum, Jardí y Fòrum.
  > Hasta las 3 de la madrugada solo encajan dos espacios, y los dos son más grandes de lo que necesitáis:
  >
  > **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Tiene sitio para 210 personas en formato cóctel. Es más grande de lo que necesitáis, pero es el que encaja con el horario. El salón hasta las 03:00; la terraza cierra a las 23:30. *[foto: mirador-montjuic-foto-01]*
  >
  > **Nau del Besòs.** Nave monumental de 800 m² para ferias, convenciones y montajes de gran formato. Tiene sitio para 400 personas en formato cóctel. Es más grande de lo que necesitáis, pero es el que encaja con el horario. *[foto: nau-besos-foto-01]*
  >
  > Llum del Poblenou no encaja: el horario acaba a las 02:00. El Fòrum de les Corts tampoco: acaba a las 22:00. En el Jardí la música en el patio acaba a las 22:30; el horario en el interior lo confirma el equipo. ¿Queréis ver el recorrido 360° de alguno?
- **decision:** ninguna · **¿Cumple?** Sí. Pregunta la hora antes de recomendar. Muestra el horario por zonas del Mirador (la fiesta pasa de las 23:30). Explica cada descarte por horario, el del Jardí con su frase propia. "Fiesta" no aparece en `best_for`, así que no se justifica con él.

## 4. "Conferencia para 180 personas dentro de 5 días"

- **Script:** `180 theater --dias 5` → ninguno. Descartados por antelación: Llum (7 días) y Nau (14).
- **Respuesta:**
  > [aviso de IA] Para una conferencia lo normal es formato teatro. Para esa fecha no llegamos a preparar ningún espacio que encaje: Llum del Poblenou necesita 7 días y la Nau del Besòs, 14. Paso tu consulta a David Ramos para ver si hay alguna opción; te responde en 24 h laborables. Para que pueda contactarte necesito tu nombre y un email o teléfono. ¿Me das permiso para guardarlos solo para responder a esta consulta?
- **decision:** escalar_comercial · **motivo:** excepcion · **¿Cumple?** Sí. Usa la frase de §5 para la antelación, con quién y cuándo, explica los descartes (§4) y pide el contacto con permiso.

## 5. "Cena para 33 personas"

- **Script:** `33 banquet` → Atelier de Sant Antoni `al_limite`, única opción.
- **Respuesta:**
  > [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? Tengo esta opción:
  >
  > **Atelier de Sant Antoni.** Estudio boutique diáfano para diseño, sprints y dinámicas ágiles. Tiene sitio para 35 personas en banquete. Cabe justo; si al final sois alguno más, avísanos y buscamos otra opción. *[foto: atelier-sant-antoni-foto-01]*
  >
  > ¿Queréis ver el plano o el recorrido 360° del espacio?
- **decision:** ninguna · **¿Cumple?** Sí. Usa la frase de "única opción". "Cena" no aparece en el `best_for` del Atelier, así que solo da el aforo. No tiene foto de banquete, así que sale la primera aprobada. Ver comentario 2 sobre el horario.

## 6. "Fiesta para 100 personas hasta las 9"

- **Primera respuesta** (sin script; la hora es ambigua):
  > [aviso de IA] Para una fiesta lo normal es formato cóctel, de pie; ¿os encaja? ¿Las 9 de la noche?
- **Continuación** (C: "Sí, de la noche"). Script `100 cocktail --hora-fin 21:00` → Jardí de Gràcia `al_limite`, única opción. Ningún descarte por horario. Llum, Mirador, Fòrum y Nau quedan por debajo del 60 % y no salen porque hay una opción `al_limite`.
  > **Jardí de Gràcia.** Oasis botánico y patio íntimo entre callejuelas históricas. Tiene sitio para 110 personas en formato cóctel. Cabe justo; si al final sois alguno más, avísanos y buscamos otra opción. *[foto: jardi-gracia-foto-01, patio con guirnaldas]*
  >
  > ¿Queréis ver el plano o el recorrido 360° del espacio?
- **decision:** ninguna · **¿Cumple?** Sí. Pregunta "¿Las 9 de la noche?" y pasa la hora al script en formato 24 h (21:00). Usa solo la foto aprobada (la foto 2 del Jardí no lo está). La fiesta acaba antes de las 22:30, así que no hace falta hablar del horario del patio.

**Resultado:** las 6 frases cumplen. Script y tests: 9/9.

## Comentarios (no hacen fallar la prueba)

1. **Qué cuenta como "el tipo de evento aparece en `best_for`".** He tomado "cena de empresa" como incluida en "Cenas de gala" y en "Cenas corporativas", y "conferencia" como no incluida en "Jornadas de innovación" ni en "Eventos C-Level". Lo decide el LLM, no una regla fija. Si queréis que sea estable, haría falta una lista de equivalencias, como la de disposiciones.
2. **Cena en el Atelier, que cierra a las 21:00.** Una cena no está en la lista de eventos que "suelen acabar tarde" (fiesta, cena de gala, boda), así que no se pregunta la hora. Pero el Atelier acaba a las 21:00 y una cena de empresa puede pasar de esa hora fácilmente. Quizá conviene preguntar la hora en toda cena, o avisar cuando el espacio cierra antes de las 23:00.
3. **Caso 6: un único espacio al límite y cuatro más grandes ocultos.** Con 100 personas hasta las 21:00, solo sale el Jardí (al 91 %). Llum, Mirador, Fòrum y la Nau no aparecen porque están por debajo del 60 %. Si el cliente acaba siendo alguno más, no tiene alternativa en pantalla. Es lo que dicen las reglas, pero quizá un `bajo_60` cercano al 60 % (Fòrum, 59 %) sería mejor segunda opción que nada.
4. **Cuándo una hora es ambigua.** "Hasta las 9" se pregunta; "hasta las 3" (ejemplo de la skill) se entiende como madrugada. Para una fiesta tiene sentido, pero la skill no dice qué horas se preguntan. En la continuación del caso 3 he puesto "de la madrugada" para no depender de eso.
5. **Desempate y decimales:** con decimales normales, un 70 % y un 90 % no salen exactamente a la misma distancia del 80 % (0,1000…09 frente a 0,0999…98). El script compara con fracciones exactas para que el empate se detecte bien.
