# Prueba router 03

Fecha: 8 de noviembre de 2026
Skill: `.claude/skills/router-intenciones/SKILL.md`, versión adaptada a la §3.2 (md5 `5fa77b005ebb442749577ea3c70fd4cf`, comprobado), con guardrails, recomendador, cualificador y consentimiento versión 3.
Scripts: `scripts/router.py` (sin `reserva`, con `accion`, `a_n8n` y `--consulta-en-marcha`; `test_router.py` 10/10), `scripts/recomendar.py` y `scripts/datos_consulta.py`.
Método: clasificación del LLM → `router.py` → respuesta con las skills que devuelve. Cada conversación empieza con **[aviso de IA]**. Datos sintéticos; no se llega a enviar nada.

## 1. "Quiero el Mirador el 14 de marzo para 100 personas"

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Quiero el Mirador el 14 de marzo para 100 personas. | Clasificación: `nuevo_evento` (antes habría sido `reserva`; decisión 8).<br>`router.py nuevo_evento` → guardrails, recomendador, cualificador (+ media y consentimiento cuando toque) · `a_n8n` **true** · ruta `lead` |
| | | `datos_consulta.py --asistentes 100 --espacio "Mirador de Montjuïc" --fecha dia` → faltan [tipo, presupuesto, necesidades] · preguntas [tipo, presupuesto] |
| B1 | [aviso de IA] Para ver si el Mirador de Montjuïc os encaja necesito saber el formato: ¿qué tipo de evento es? ¿Y tenéis un presupuesto aproximado? | §3: falta la disposición, así que se pregunta antes de validar (el tipo de evento la da). Una pregunta del recomendador y otra del cualificador: dos en total |
| C2 | Una cena de empresa. Unos 5.000 €. | Cena → `banquet`. Presupuesto dado. Una cena suele acabar tarde: el recomendador pregunta la hora antes de validar |
| B2 | Para una cena lo normal es formato banquete; ¿os encaja? ¿Y hasta qué hora más o menos? | Recomendador §1 |
| C3 | Sí, hasta la 1. | "La 1", sin más contexto → madrugada → 01:00 |
| | | `recomendar.py --validar sp-mirador-montjuic --asistentes 100 --disposicion banquet --dias 126 --hora-fin 01:00` → **encaja**, sin motivos (`comodo`).<br>`datos_consulta.py … --presupuesto "unos 5.000 €" --preguntados tipo,presupuesto` → faltan [necesidades] |
| B3 | El Mirador de Montjuïc os encaja: tiene sitio para 120 personas en banquete. Salón panorámico con terraza privada y vistas al mar y al puerto. El salón hasta las 03:00; la terraza cierra a las 23:30. *[imagen: mirador-montjuic-foto-02, Imagen ilustrativa]* ¿Necesitaréis algo especial, como catering o audiovisuales? | Validación del script + la pregunta que queda del cualificador. El aviso de la terraza **no lo da `--validar`**: lo he sacado de los datos (ver comentario 1) |
| C4 | Solo un DJ. | Necesidades: "DJ" → `listo_para_enviar` **true** |
| B4 | Para que el equipo te envíe la propuesta necesito tu nombre y tu email. ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad? | Consentimiento §4. Fin de la prueba |

- **¿Cumple?** **Sí.**
  - Espacio y fecha concretos ya no son `reserva`: van como `nuevo_evento`.
  - El recomendador valida el espacio elegido antes de nada y el cualificador sigue con lo que falta (§3).
  - Nunca hay más de dos preguntas por mensaje, ni bloqueo ni disponibilidad.
  - `preferred_location` sería "Mirador de Montjuïc" y `event_date` 2027-03-14.
- **Pero:** el aviso de la terraza no sale del script (comentario 1).

## 2. "Quiero quejarme de mi última cena y organizar otra"

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Quiero quejarme de mi última cena y organizar otra. | Clasificación: `queja`, `nuevo_evento`.<br>`router.py queja nuevo_evento` → orden [queja, nuevo_evento] · skills guardrails, recomendador, cualificador · `escalar_humano`, `queja` · `accion` **contacto_equipo** · `a_n8n` **true** · ruta `incidencia` · `rutas_adicionales` [`lead`] |
| B1 | [aviso de IA] Siento que la última cena no saliera bien. Para la reclamación, escribe al equipo en atencion@empresa-eventos.example o llama al +34 930 000 000. Y sobre la nueva cena, ¿para cuántas personas sería? | Frase de la §5 de la skill, tal cual. `datos_consulta.py --tipo cena` → preguntas [asistentes, espacio_o_zona]; se hace una |
| C2 | Seríamos unos 60. | La consulta sigue su camino normal (recomendador → cualificador → consentimiento → envío) |

- **¿Cumple?** **Sí.**
  - La queja no va a n8n y no se piden datos para ella: contacto del equipo, sin plazos.
  - El lead queda en `rutas_adicionales`, y `a_n8n` es true porque la consulta nueva sí acabará en un envío.
- **Nota:** la frase de la §5 no dice el horario del equipo (de lunes a sábado, de 9 a 18 h), que la §2 sí pone junto al contacto. He usado la frase de la §5 tal cual.

## 3. "Quiero hablar con una persona" a mitad de una consulta

Conversación en marcha: cena de empresa para 120 en marzo, el cliente ya ha elegido el Llum del Poblenou y no sabe el día (como en la prueba cualificador 03, después de C3).

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C | Prefiero hablar con una persona. | Clasificación: `persona`, con una consulta en marcha.<br>`router.py persona --consulta-en-marcha` → skills guardrails · `escalar_humano`, `peticion_humano` · `accion` **ofrecer_envio** · `a_n8n` **true** · ruta `lead`.<br>`datos_consulta.py` todavía daba [presupuesto, necesidades]: no se preguntan, porque se ofrece cerrar ya |
| B | Claro. Si quieres, cierro ya tu consulta y se la paso al equipo, que te escribirá por email. Para eso necesito tu nombre y tu email: ¿aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad? Si lo prefieres, también puedes escribir al equipo en atencion@empresa-eventos.example o llamar al +34 930 000 000 (de lunes a sábado, de 9 a 18 h). | Tabla §2: se ofrece cerrar y enviar ya, y además el contacto del equipo. La pregunta de privacidad es la de consentimiento §4 |

- **¿Cumple?** **Sí:** se ofrece el envío y el contacto, sin plazos, y no se promete ninguna llamada inmediata.
- **Pero:**
  - `router.py` no incluye consentimiento en las skills, aunque ofrecer el envío obliga a hacer la pregunta de privacidad (comentario 2).
  - He evitado "te llegará un email para reservar la llamada". En el flujo de Ale, el email con Calendly solo sale si el lead es lo bastante bueno, hay fecha y hay espacio (comentario 3).

**Resultado:** las 3 conversaciones cumplen la skill nueva. Quedan los puntos de abajo.

## Comentarios

1. **`--validar` no devuelve `avisos_zona`.** La recomendación normal sí lo devuelve, pero la validación del espacio elegido no. En el caso 1 (Mirador hasta la 1), el aviso de la terraza lo he tenido que sacar de los datos, justo lo que la regla 3 deja al script. Es para el punto 6 (recomendador).
2. **`persona` con consulta en marcha sin consentimiento.** El script devuelve `ofrecer_envio` y `a_n8n` true, pero solo guardrails como skill. Si el cliente acepta, hace falta consentimiento (pregunta de privacidad) y la skill de envío. Siguiendo vuestra indicación ("persona ya no lleva consentimiento"), no lo he añadido.
3. **La promesa del email.** La frase de `escalar_comercial` en KNOWLEDGE §3.1 ("en unos minutos te llegará un email para reservarla") y la respuesta al 202 dan por hecho que siempre llega el email con Calendly. En el flujo de Ale no siempre llega: sin fecha, sin espacio o con un lead flojo, lo contacta una persona.
4. **"Cerrar ya" con datos pendientes.** En el caso 3 faltaban presupuesto y necesidades. La skill dice que se ofrece enviar ya, así que se envía sin preguntarlos, pero no lo dice de forma explícita (ni la del cualificador).
5. **La §1 de la skill remite a "la prioridad de la §4"**, pero la prioridad está en la §5. No lo he cambiado.
