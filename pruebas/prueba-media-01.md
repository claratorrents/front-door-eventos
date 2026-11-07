# Prueba media 01

Fecha: 7 de noviembre de 2026
Skill: `.claude/skills/media-espacios/SKILL.md` (versión del equipo, md5 `adac167191545d7e27f0de58d29fca62`, comprobado), junto con guardrails y recomendador-espacios.
Script: `scripts/recomendar.py` devuelve la foto de cada tarjeta (`test_recomendar.py`: 14/14). Además he comprobado que en 1.600 combinaciones (1 a 400 personas × 4 disposiciones) nunca devuelve una foto no aprobada.
Datos: `disposition` en las 12 fotos; el validador la exige en las aprobadas.
Método: Claude Code responde como el chatbot. La primera frase abre la conversación (**[aviso de IA]**); las demás van a mitad de conversación. Las imágenes se indican como *[imagen: id]* (el chat web las mostrará por id, nunca con la ruta). Pie = `description` tal cual.

| # | Frase | Respuesta | Material enseñado | ¿Cumple? |
|---|---|---|---|---|
| 1 | Cena para 120 | B1: [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? ¿Y hasta qué hora más o menos?<br>C: Banquete, hasta las 00:00.<br>B2: **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Encaja para una cena. *[imagen: llum-poblenou-foto-01]* Pie: "Nave industrial montada para cena de gala, con luz cenital".<br>**Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Encaja para una cena. El salón hasta las 03:00; la terraza cierra a las 23:30. Cabe justo; si podéis ser alguno más, mejor el Llum del Poblenou. *[imagen: mirador-montjuic-foto-02]* Pie: "Salón acristalado en montaje banquete".<br>¿Queréis ver el plano o el recorrido 360° de alguno? | Llum foto-01 (`banquet`), Mirador foto-02 (`banquet`), las que da el script | Sí. Una foto por espacio, de banquete, elegida por el script, con su `description` como pie y una sola pregunta final |
| 2 | ¿Tenéis más fotos del Jardí de Gràcia? | Esta es la foto que tenemos del Jardí de Gràcia: *[imagen: jardi-gracia-foto-01]* Pie: "Patio ajardinado con olivos y guirnaldas encendidas". Si quieres, también te enseño el plano o el recorrido 360°. | Solo foto-01 (la foto-02 no está aprobada) | Sí. No enseña ni menciona la foto 2 |
| 3 | ¿Tenéis vídeo de la Nau? | No tenemos vídeo de este espacio, pero sí un recorrido virtual 360°. ¿Te lo enseño? | Nada todavía; se ofrece el tour | Sí. Frase fija de §4 |
| 4 | ¿Tenéis fotos del patio del Jardí de noche? | No tenemos fotos del patio de noche; tengo esta del patio con las guirnaldas encendidas. ¿Te sirve? *[imagen: jardi-gracia-foto-01]* Pie: "Patio ajardinado con olivos y guirnaldas encendidas". | foto-01 | Sí. Dice que no lo tiene, ofrece lo que hay y no describe más allá de la `description` |
| 5 | Enséñame el plano del Mirador | Aquí tienes el plano del Mirador de Montjuïc: *[enlace: mirador-montjuic-plano]* "Plano del pabellón, la terraza y el parking". | mirador-montjuic-plano (aprobado) | Sí. Se da como enlace, con su `description`, sin la ruta |

**Resultado:** las 5 frases cumplen. Tests: 14/14. Validador: todo correcto.

## Comentarios

1. **"Imagen ilustrativa" (§5) no tiene dato.** La skill pide indicarlo cuando la imagen es generada con IA o de relleno, pero en `espacios.json` no hay ningún campo que lo diga. Hoy todas las rutas están en `/media/placeholders/`, así que todas son de relleno, y con el pendiente de KNOWLEDGE (fotos generadas con IA) lo seguirán siendo. En las respuestas de arriba no he puesto "Imagen ilustrativa", porque deducirlo de la ruta sería suponer. Haría falta un campo (por ejemplo `illustrative: true`) para que la regla no dependa del LLM.
2. **Foto de la terraza del Mirador en eventos que pasan de las 23:30.** En una fiesta hasta las 3, la tarjeta del Mirador lleva la foto-01 (`cocktail`, la terraza al atardecer), mientras el aviso dice que la terraza cierra a las 23:30. El cliente ve la terraza como imagen del espacio en un evento en el que no la podrá usar después de esa hora. Lo dicen las reglas, pero choca.
3. **Mirador para una conferencia:** no tiene foto de teatro, así que sale la primera aprobada (la terraza, `cocktail`). Es lo que dice la regla; solo apunto que la imagen no muestra el montaje que piden.
4. **Lo que se pide después lo elige el LLM.** "Más fotos", plano y tour se buscan en los datos sin script. Filtrar por `approved: true` es sencillo, pero si queréis la misma garantía que en la tarjeta, se podría añadir una función al script (por ejemplo `media_aprobada(espacio, tipo)`).
5. **El script devuelve la foto con `id` y `description`, sin la `url`.** Así el LLM nunca tiene la ruta delante. El chat web tendrá que buscar la imagen por id cuando la muestre.
6. **"¿Tenéis más fotos?" del Jardí** devuelve una sola foto. Es correcto, pero "esta es la foto que tenemos" puede sonar pobre. Es una cuestión de datos (solo hay una aprobada), no de la skill.
