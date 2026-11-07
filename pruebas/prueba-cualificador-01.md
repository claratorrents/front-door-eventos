# Prueba cualificador 01

Fecha: 7 de noviembre de 2026
Skill: `.claude/skills/cualificador-leads/SKILL.md` (versión del equipo, md5 `b519934851877b209861724d117e62b0`, comprobado), junto con guardrails, consentimiento y recomendador-espacios.
Scripts: `scripts/puntuar_lead.py` (`test_puntuar_lead.py`: 5/5) y `scripts/recomendar.py` (`test_recomendar.py`: 11/11).
Método: Claude Code responde como el chatbot en conversaciones completas. **[aviso de IA]** abrevia el aviso del primer mensaje. Los datos del cliente aparecen como `[empresa]`, `[nombre]` y `[email]`. La puntuación y la ocupación solo aparecen en las líneas "Script" (dato interno). Antelación calculada con la fecha real de hoy (7/11/2026).

## 1. Cena de 120: primero sin día, después "el 14 de marzo"

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Cena de empresa para 120 personas en marzo, unos 6.000 €, somos de [empresa], decidimos esta semana. | |
| B1 | [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? ¿Y hasta qué hora más o menos? | Cena → se pregunta la hora antes de recomendar (recomendador §1). Aún sin script |
| C2 | Banquete, sí. Hasta las 00:00. | |
| B2 | **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Encaja para una cena. *[foto: llum-poblenou-foto-01]*<br>**Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Encaja para una cena. El salón hasta las 03:00; la terraza cierra a las 23:30. Cabe justo; si podéis ser alguno más, mejor el Llum del Poblenou. *[foto: mirador-montjuic-foto-02]*<br>¿Tenéis ya un día concreto? Así puedo reservaros la fecha de forma provisional. | `recomendar 120 banquet --hora-fin 00:00` → Llum `comodo`, Mirador `al_limite` (aviso terraza 23:30).<br>`puntuar_lead`: fecha mes 15 · asistentes 20 · presupuesto 20 · tipo 15 (cena en `event_types` de Llum) · empresa 10 · urgencia 10 = **90** → `escalar_comercial`; faltan `dia_exacto`, `espacio_elegido`, `antelacion_cumplida`. Falta el día → se pregunta antes de escalar |
| C3 | El 14 de marzo, y nos quedamos con el Llum. | |
| B3 | Lo compruebo con el calendario y te digo enseguida. | Antelación: 127 días ≥ 7 (Llum) → cumplida.<br>`puntuar_lead` con día exacto + espacio elegido + antelación = **100** → `prerreserva`.<br>`consulta_disponibilidad` → n8n: libre (SIMULADO) |
| B4 | Según el calendario, ese día parece libre. Te lo confirma el comercial. Puedo bloquear el Llum del Poblenou para el 14 de marzo de forma provisional y sin compromiso durante 72 h laborables. En ese plazo, Marta Soler te envía la propuesta con precio y condiciones. ¿Lo bloqueo? | Frase de bloqueo de la skill §3 |
| C4 | Sí. | "Sí" explícito al bloqueo |
| B5 | Para hacerlo necesito tu nombre y un email o teléfono (el que prefieras); la empresa ya me la has dicho. ¿Me das permiso para guardarlos solo para responder a esta consulta? | Consentimiento §3–§4 |
| C5 | Sí: [nombre], [email]. | Apunte `otorgado` (finalidad "responder a la consulta", datos nombre, email, empresa) |
| B6 | Gracias. He pedido el bloqueo provisional del Llum del Poblenou para el 14 de marzo; Marta Soler te lo confirma y te envía la propuesta en 72 h laborables. Una última cosa: ¿quieres recibir novedades de espacios y eventos? Es opcional. | `decision: prerreserva` (bloqueo SIMULADO; ver comentario 1). Publicidad, una vez, justo después de la acción principal |

**¿Cumple?** Sí.
- **Datos:** se recogen con una o dos preguntas por mensaje y sin cuestionario seguido.
- **Puntuación:** se calcula con el script, se vuelve a calcular cuando llegan el día y el espacio, y nunca se muestra.
- **Día exacto:** como faltaba, se pregunta antes de escalar.
- **Bloqueo:** se ofrece solo cuando se cumplen las 4 condiciones, después de comprobar la disposición, y pide un "sí" explícito y el contacto con permiso.
- **Sin día:** si en C3 el cliente hubiera dicho "aún no tenemos día", la respuesta sería: "Paso tu consulta a Marta Soler, que te enviará una propuesta a medida en 24 h laborables." Después se pide el contacto con permiso (`escalar_comercial`, `lead`).

## 2. Boda

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Boda para unas 100 personas el año que viene, aún no sabemos presupuesto. | |
| B1 | [aviso de IA] Para una boda lo normal es formato banquete; ¿os encaja? ¿Y hasta qué hora más o menos? | Boda → se pregunta la hora |
| C2 | Banquete. Hasta la 1. | "La 1" → de 1 a 7 = madrugada → 01:00 |
| B2 | **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Tiene sitio para 120 personas en banquete. El salón hasta las 03:00; la terraza cierra a las 23:30. *[foto: mirador-montjuic-foto-02]*<br>**Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Tiene sitio para 150 personas en banquete. *[foto: llum-poblenou-foto-01]*<br>¿Es una celebración familiar, o hay alguna empresa detrás? ¿Y para cuándo necesitáis decidirlo? | `recomendar 100 banquet --hora-fin 01:00` → Mirador `comodo` (aviso terraza), Llum `comodo`.<br>"Boda" no está en `event_types` → solo el dato |
| C3 | Familiar. Sin prisa. | |
| B3 | Perfecto. Paso vuestra consulta a Marta Soler, que os enviará una propuesta a medida en 24 h laborables. Para que pueda contactaros necesito tu nombre y un email o teléfono. ¿Me das permiso para guardarlos solo para responder a esta consulta? | `puntuar_lead`: fecha año 5 · asistentes aproximado 10 · presupuesto 0 · tipo 10 (boda no está en `event_types` del Mirador) · empresa particular 5 · urgencia 0 = **30** → `escalar_comercial`, `lead`. Comercial del primer espacio (Mirador) = Marta Soler |

**¿Cumple?** Sí.
- **Puntuación:** 30, la que calculasteis.
- **Presupuesto:** no se insiste ("no lo sabe" puntúa 0).
- **Empresa y urgencia:** se preguntan juntas, en un solo mensaje con dos preguntas.
- **Decisión:** pasa al comercial del primer espacio recomendado, con su plazo, y pide el contacto con permiso.
- **Tarjetas:** no se justifican con `best_for`, porque "boda" no está en `event_types`.

**Resultado:** las dos conversaciones cumplen. Tests: cualificador 5/5 y recomendador 11/11.

## Comentarios

1. **¿Qué se dice después del "sí" al bloqueo?** La skill da la frase para ofrecer el bloqueo, pero no la de después. Mientras n8n esté simulado, el bloqueo también es SIMULADO, y decir "Bloqueado" sería presentarlo como confirmado (guardrails, regla 2). He usado "He pedido el bloqueo provisional…; Marta Soler te lo confirma…". Haría falta una frase fija.
2. **"Unos" no puntúa igual en los dos campos.** En el ejemplo de la skill, "unos 6.000 €" puntúa como cifra concreta (20), pero "unas 100 personas" puntúa como aproximado (10). Si "unos" significa aproximado, el presupuesto debería ser "rango u orientativo" (10) y la cena sumaría 80, no 90. Con 80 y día exacto llegaría a 90 y la decisión no cambiaría, pero el criterio tiene que ser el mismo en los dos campos.
3. **"Si solo falta el día exacto, se pregunta":** en la cena faltaban el día y la elección de espacio, y la antelación depende de los dos. Lo he leído como "si falta el día, se pregunta antes de escalar". El script devuelve `condiciones_que_faltan` para que la decisión no dependa del LLM, pero la skill no dice qué hacer cuando faltan varias condiciones.
4. **El tipo depende del primer espacio recomendado.** Si el cliente elige el segundo (por ejemplo, el Mirador para una boda), el tipo se sigue puntuando con el primero. Tampoco está definido qué nivel de tipo se usa cuando no hay ningún espacio recomendado.
5. **Lo que todavía decide el LLM:** traducir las frases a niveles. Por ejemplo, si "este mes" es menos de 2 semanas o menos de un mes depende del día en que se diga, y si hay "empresa identificada". El script es estable, pero la entrada no. Una lista de frases → nivel, como la de disposiciones, lo haría más fijo.
6. **Día exacto:** el script no lo recibe aparte; lo saca del nivel de fecha (`dia_exacto`) para que las dos entradas no puedan contradecirse. Pedisteis "si hay día exacto" como entrada; si lo preferís separado, se cambia.
7. **Antelación:** se calcula con la fecha real (hoy, 7/11/2026). El chat web tendrá que pasar la fecha del sistema, igual que la hora.
