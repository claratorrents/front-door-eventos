# Prueba router 02

Fecha: 7 de noviembre de 2026
Skill: `.claude/skills/router-intenciones/SKILL.md` con los cambios de esta ronda (fila `reserva` con recomendador, consentimiento en los escalados, reglas nuevas en §3 y §4).
Script: `scripts/router.py` con `rutas_adicionales` y la ruta de `persona` tomada de la otra intención. `test_router.py`: **12/12**. `recomendar.py` con validación del espacio elegido (`--validar`); `test_recomendar.py`: **24/24**. Cualificador 10/10, validador correcto.
Método: igual que la prueba 01: clasificación del LLM → `router.py` → respuesta con las skills que devuelve. Cada frase abre la conversación (**[aviso de IA]**).

## 1. "Quiero bloquear el Mirador para 300 personas el 14 de marzo" (primera pasada)

- **Clasificación:** `reserva` (espacio y fecha concretos).
- **`router.py reserva`:** skills guardrails, cualificador, **recomendador**, consentimiento · ruta `reserva` · `rutas_adicionales` [].
- **Recomendador:** no dice disposición ni tipo de evento. Para 300 personas, `recomendar.py` (antelación: 127 días) da:
  - `cocktail` → Nau del Besòs (`comodo`);
  - `theater` → Nau del Besòs (`al_limite`);
  - `banquet` y `classroom` → ninguno.
  
  En ningún caso sale el Mirador, cuyo aforo máximo es 210 (cóctel).
- **Respuesta:**
  > [aviso de IA] El Mirador de Montjuïc no tiene sitio para 300 personas: en su formato más amplio, el cóctel, caben 210. Para 300, el espacio que encaja es la Nau del Besòs (hasta 400 personas en cóctel o 300 en teatro). ¿Qué tipo de evento es?
- **decision:** ninguna (todavía no hay bloqueo: falta espacio válido y datos) · **¿Cumple?** **En parte.**
  - La respuesta sigue la regla nueva de §3: explica el motivo del descarte y propone la alternativa que da el script, sin bloquear el Mirador.
  - **Pero el motivo no lo da el script.** `recomendar.py` solo devuelve los descartes por antelación u horario; los de aforo no salen (recomendador §2, regla 7). Que el Mirador no aparezca en la salida no basta para saber por qué: un espacio también desaparece si queda por debajo del 60 %. Para escribir "caben 210" he tenido que mirar el aforo en los datos y decidir el motivo yo, que es justo lo que la regla 3 de `AGENTS.md` deja al script (ver comentario 1).

## 1b. El mismo caso, repetido con la validación del script

Cambios: `recomendar.py --validar` comprueba el espacio elegido y devuelve todos los motivos con el dato que falla, más las alternativas. La skill dice ahora "Si la validación del script descarta el espacio elegido…".

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Quiero bloquear el Mirador para 300 personas el 14 de marzo. | `reserva` → `router.py`: guardrails, cualificador, recomendador, consentimiento · ruta `reserva` |
| B1 | [aviso de IA] Para ver si el Mirador de Montjuïc os encaja necesito saber el formato: ¿qué tipo de evento es? | Falta la disposición, que es obligatoria para validar (recomendador §1). No se valida todavía |
| C2 | Un cóctel. | Cóctel → `cocktail` |
| B2 | El Mirador de Montjuïc no encaja para 300 personas: en cóctel caben 210. Para 300 en cóctel, el espacio que encaja es la Nau del Besòs, que tiene sitio para 400 personas en formato cóctel. *[imagen: nau-besos-foto-01, Imagen ilustrativa]* ¿Queréis que miremos la Nau para el 14 de marzo? | `recomendar.py --validar sp-mirador-montjuic --asistentes 300 --disposicion cocktail --dias 127` → `encaja: false`; motivos: `aforo` (en cocktail caben 210; se piden 300); alternativas: Nau del Besòs (`comodo`). La antelación (10 días) se cumple, así que no aparece como motivo |

- **decision:** ninguna (todavía no hay bloqueo) · **¿Cumple?** **Sí.**
  - **Motivo y dato:** "en cóctel caben 210" sale del script, que también dice que la antelación se cumple.
  - **Alternativa:** la Nau la propone el script, no el LLM.
  - **Sin bloqueo:** no se ofrece bloquear el Mirador.
  - **Disposición:** se pregunta antes de validar, porque sin ella el script no puede comprobar el aforo.

## 2. "Quiero quejarme de mi última cena y organizar otra"

- **Clasificación:** `queja`, `nuevo_evento`.
- **`router.py queja nuevo_evento`:** orden [queja, nuevo_evento] · skills guardrails, consentimiento, recomendador, cualificador · `escalar_humano`, `queja` · ruta `incidencia` · `rutas_adicionales` [**lead**].
- **Conversación:**
  > B1: [aviso de IA] Siento que la última cena no fuera bien. Paso tu reclamación al equipo de atención al cliente, que te responde en 24 h laborables. Y sobre la nueva cena, ¿para cuántas personas sería?
  >
  > C: Seríamos 60.
  >
  > B2: Para que el equipo de atención y el comercial puedan contactarte, necesito tu nombre y un email o teléfono. ¿Me das permiso para guardarlos solo para responder a estas dos consultas? Y para la cena, ¿sería en banquete y hasta qué hora más o menos?
- **¿Cumple?** Sí.
  - **Primer mensaje:** reconoce la queja (quién responde y en qué plazo) y hace una sola pregunta del evento.
  - **Contacto:** se pide una sola vez, en el mensaje siguiente, y sirve para los dos temas (§4).
  - **Preguntas:** dos en cada mensaje. He juntado la disposición y la hora de la cena en una sola pregunta.
  - **Lead:** queda registrado en `rutas_adicionales`.

## 3. "Queremos un cóctel para 80 y, por cierto, borrad mi email antiguo"

- **Clasificación:** `nuevo_evento`, `privacidad`.
- **`router.py privacidad nuevo_evento`:** orden [privacidad, nuevo_evento] · skills guardrails, consentimiento, recomendador, cualificador · ruta `privacidad` · `rutas_adicionales` [**lead**].
- **Respuesta:**
  > [aviso de IA] Para encontrar tus datos necesito el email o teléfono que usaste; lo usamos solo para esto. El equipo de atención te lo confirma en 24 h laborables. Y sobre el cóctel para 80: **Jardí de Gràcia.** Oasis botánico y patio íntimo entre callejuelas históricas. Hasta 110 personas en cóctel. Encaja para un cóctel de networking. *[imagen: jardi-gracia-foto-01, Imagen ilustrativa]* ¿Para qué fecha sería?
- **¿Cumple?** Sí. Primero privacidad (consentimiento §8: `escalar_humano`, `privacidad`, apunte `borrado_solicitado`) y después el evento (`recomendar 80 cocktail` → Jardí `comodo`). El lead ya no se pierde: aparece en `rutas_adicionales`.

**Resultado:** en la primera pasada, 2 de 3 cumplieron y 1 en parte (caso 1: el motivo del descarte por aforo no salía del script). Con la validación del script, el caso 1b cumple: **las 3 frases cumplen**.

## Comentarios

1. **Resuelto en 1b: el recomendador valida el espacio elegido.** La regla nueva de §3 ("Si el recomendador descarta el espacio elegido (aforo, antelación u horario), se explica el motivo…") necesita que el script diga **por qué** se descarta. Hoy solo lo dice para antelación y horario. Una opción: que `recomendar.py` acepte `--espacio-elegido` y devuelva su validación (`valido: sí/no`, `motivo: aforo / antelacion / horario`, y el aforo en la disposición pedida, o el máximo si no se sabe la disposición). El equipo lo pidió después de la primera pasada: `recomendar.py --validar` devuelve `encaja`, todos los motivos con su dato y las alternativas.
2. **Disposición desconocida en `reserva`.** En la primera pasada usé el formato más amplio (cóctel) para explicar el descarte. En 1b se pregunta antes de validar, porque el recomendador la pide como dato obligatorio (§1). La skill del router no lo dice de forma explícita.
3. **`rutas_adicionales` sin repetidos.** El script no repite la ruta principal ni las ya listadas. Por ejemplo, `reserva` + `nuevo_evento` da ruta `reserva` y `rutas_adicionales` [`lead`]; `persona` + `nuevo_evento` da ruta `lead` y `rutas_adicionales` vacía, porque las dos son `lead`.
