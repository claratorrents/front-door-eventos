---
name: router-intenciones
description: Primer paso con cada mensaje del cliente. Clasifica la intención en una lista cerrada (informacion, nuevo_evento, cambio_reserva, queja, privacidad, persona, fuera_tema) y, con scripts/router.py, decide qué skills entran, qué ruta se registra, si la conversación acabará en un envío a n8n y qué intención se atiende primero si hay varias. Si duda entre intenciones que llevan a acciones distintas, pregunta. No responde por sí mismo al cliente ni se usa en tareas de desarrollo.
---

# Router de intenciones

Se aplica antes que las demás skills, en cada mensaje del cliente. Contexto en `KNOWLEDGE.md` §3.2.

## 1. Reparto: el LLM clasifica, las reglas deciden
- El LLM **solo clasifica** el mensaje en una o varias intenciones de la §2. No puede inventar otras.
- **Lo que se hace con cada intención** (skills, decisión, ruta, envío a n8n y orden) lo devuelve `scripts/router.py` con la tabla de la §2 y la prioridad de la §5. El LLM no lo cambia.
- La intención es un dato interno: nunca se dice al cliente.

## 2. Intenciones y qué pasa con cada una

| Intención | Señales | Qué pasa | ¿Va a n8n? | `ruta` |
|---|---|---|---|---|
| `informacion` | Pregunta sobre un espacio o una política sin plan de evento ("¿Tenéis parking en el Fòrum?") | Guardrails + datos del espacio; media si pide fotos, plano o tour. Si no hay dato: contacto del equipo, sin plazos | No | `informacion` |
| `nuevo_evento` | Quiere organizar algo, aunque ya diga espacio y fecha ("Queremos una cena para 120", "Quiero el Mirador el 14 de marzo") | Recomendador + cualificador; media cuando toque; al final, consentimiento y envío a n8n | Sí, una vez, al final | `lead` |
| `cambio_reserva` | Habla de una reserva que ya tiene ("Necesito cambiar la fecha de mi reserva", "Quiero cancelar") | Contacto del equipo, sin plazos ni datos. `escalar_humano`, motivo `cambio_reserva` | No | `cambio` |
| `queja` | Reclamación o problema legal ("Quiero poner una reclamación") | Contacto del equipo, sin plazos ni datos. `escalar_humano`, motivo `queja` (o `legal`) | No | `incidencia` |
| `privacidad` | Ver, borrar o dejar de usar sus datos ("Borrad mis datos") | Consentimiento §8 | No | `privacidad` |
| `persona` | Pide hablar con alguien ("Quiero hablar con una persona") | Sin consulta en marcha: contacto del equipo. Con consulta en marcha: se ofrece cerrar y enviar la consulta ya, y además el contacto del equipo. Si acepta, se envía con lo que haya, sin preguntar más datos (solo la pregunta de privacidad). `escalar_humano`, motivo `peticion_humano` | Solo si acepta enviar la consulta | la del tema; si no hay, `incidencia` |
| `fuera_tema` | Nada que ver con eventos ni espacios ("¿Qué tiempo hará mañana?") | Guardrails, regla 8 | No | `fuera_tema` |

- Guardrails se aplica siempre, además de lo que diga la tabla.
- Contacto del equipo: atencion@empresa-eventos.example · +34 930 000 000 (de lunes a sábado, de 9 a 18 h). Sin prometer plazos (KNOWLEDGE §3.2, decisión 7).
- La antigua intención `reserva` se junta con `nuevo_evento` (decisión 8): ya no hay bloqueos.

## 3. Dentro de un `nuevo_evento`: quién pregunta primero
1. **Recomendador:** lo que necesita para recomendar (asistentes, disposición y, si hace falta, hora de fin).
2. **Tarjetas** de espacios.
3. **Cualificador:** el resto de datos (espacio elegido o zona, fecha, presupuesto, necesidades).
4. **Consentimiento** (pregunta de privacidad) y **envío a n8n**.
- **Máximo dos preguntas por mensaje entre todas las skills.** Si el recomendador pregunta una cosa, el cualificador solo puede añadir otra.
- Si el cliente ya dice espacio y fecha, el recomendador valida ese espacio con el script. Si lo descarta (aforo, antelación u horario), se explica el motivo y se proponen las alternativas que dé el script. Si falta la disposición, se pregunta antes de validar.

## 4. Casos especiales
- **Solo un saludo** ("Hola", "Buenas"): no es una intención. Aviso de IA (skill consentimiento) y "¿Qué evento tenéis en mente?". La ruta se decide con el siguiente mensaje.
- **Conversación en marcha:** se mantiene la intención anterior mientras el cliente siga con lo mismo. Si aparece una intención nueva, se vuelve a clasificar.
- **Información dentro de un evento** ("¿Y tiene parking?"): se responde y se sigue con `nuevo_evento`. No cambia la ruta.
- **Frustración** con una consulta en marcha: igual que `persona` con consulta en marcha.

## 5. Varias intenciones en un mismo mensaje
`scripts/router.py` las ordena por esta prioridad:
1. `privacidad`
2. `queja`
3. `persona`
4. `cambio_reserva`
5. `nuevo_evento`
6. `informacion`
7. `fuera_tema`

- Se responde primero a la más prioritaria y se retoma lo demás en el mismo mensaje.
- La `ruta` registrada es la de la más prioritaria; las demás van en `rutas_adicionales`.
- Si `persona` va con otra intención, la ruta del tema es la de esa otra intención.
- **Queja y evento nuevo:** la queja no va a n8n; la consulta nueva sigue su camino normal. "Siento que la última cena no saliera bien. Para la reclamación, escribe al equipo en atencion@empresa-eventos.example o llama al +34 930 000 000. Y sobre la nueva cena, ¿para cuántas personas sería?"

## 6. Si duda
- Si el mensaje encaja en dos intenciones que llevan a **acciones distintas**, se pregunta en vez de suponer, con opciones concretas: "¿Quieres organizar un evento nuevo o es sobre una reserva que ya tienes?"
- Si las dos llevan a lo mismo, no se pregunta.
- Si después de preguntar sigue sin estar claro, se trata como `persona` (contacto del equipo).

## 7. Ejemplos
- "Hola" → saludo: aviso de IA + "¿Qué evento tenéis en mente?"
- "Queremos una cena de empresa para 120 en marzo" → `nuevo_evento`, ruta `lead`, acabará en envío a n8n
- "Quiero el Mirador el 14 de marzo para 100 personas" → `nuevo_evento`; el recomendador valida el Mirador y el cualificador sigue con lo que falte
- "¿Tenéis parking en el Fòrum?" → `informacion`
- "Necesito cambiar la fecha de mi reserva" → `cambio_reserva` → contacto del equipo
- "Quiero quejarme de mi última cena y organizar otra" → `queja` primero (contacto del equipo), después `nuevo_evento`; ruta `incidencia`, `rutas_adicionales` [`lead`]
- "Quiero hablar con una persona" a mitad de una consulta → se ofrece enviar la consulta ya + contacto del equipo
- "¿Qué tiempo hará mañana?" → `fuera_tema`
