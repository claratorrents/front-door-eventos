---
name: router-intenciones
description: Primer paso con cada mensaje del cliente. Clasifica la intención en una lista cerrada (informacion, nuevo_evento, reserva, cambio_reserva, queja, privacidad, persona, fuera_tema) y, con scripts/router.py, decide qué skills entran, qué ruta se registra y qué intención se atiende primero si hay varias. Si duda entre intenciones que llevan a acciones distintas, pregunta. No responde por sí mismo al cliente ni se usa en tareas de desarrollo.
---

# Router de intenciones

Se aplica antes que las demás skills, en cada mensaje del cliente. Contexto en `KNOWLEDGE.md`.

## 1. Reparto: el LLM clasifica, las reglas deciden
- El LLM **solo clasifica** el mensaje en una o varias intenciones de la §2. No puede inventar otras.
- **Lo que se hace con cada intención** (skills, decisión, ruta y orden) lo devuelve `scripts/router.py` con la tabla de la §2 y la prioridad de la §4. El LLM no lo cambia.
- La intención es un dato interno: nunca se dice al cliente.

## 2. Intenciones y qué pasa con cada una

| Intención | Señales | Qué pasa | `ruta` |
|---|---|---|---|
| `informacion` | Pregunta sobre un espacio o una política sin plan de evento ("¿Tenéis parking en el Fòrum?", "¿Hasta qué hora hay música en la Nau?") | Guardrails + datos del espacio; media si pide fotos, plano o tour | `informacion` |
| `nuevo_evento` | Quiere organizar algo ("Queremos una cena para 120", "Buscamos sitio para una formación") | Recomendador + cualificador (+ media y consentimiento cuando toque) | `lead` |
| `reserva` | Quiere bloquear un espacio **y** una fecha concretos ("Quiero bloquear el Llum el 14 de marzo") | Cualificador (condiciones del bloqueo) + recomendador (valida el espacio elegido) + consentimiento | `reserva` |
| `cambio_reserva` | Habla de una reserva que ya tiene ("Necesito cambiar la fecha de mi reserva", "Quiero cancelar") | `escalar_humano`, motivo `cambio_reserva` + consentimiento para el contacto | `cambio` |
| `queja` | Reclamación o problema legal ("Quiero poner una reclamación", "Esto incumple el contrato") | `escalar_humano`, motivo `queja` (o `legal` si es un tema legal) + consentimiento para el contacto | `incidencia` |
| `privacidad` | Ver, borrar o dejar de usar sus datos ("Borrad mis datos") | Consentimiento §8 | `privacidad` |
| `persona` | Pide hablar con alguien ("Quiero hablar con una persona") | `escalar_humano`, motivo `peticion_humano` + consentimiento para el contacto | la del tema de la conversación; si no hay, `incidencia` |
| `fuera_tema` | Nada que ver con eventos ni espacios ("¿Qué tiempo hará mañana?") | Guardrails, regla 8 | `fuera_tema` |

Guardrails se aplica siempre, además de lo que diga la tabla.

## 3. Casos especiales
- **Solo un saludo** ("Hola", "Buenas"): no es una intención. Aviso de IA (skill consentimiento) y "¿Qué evento tenéis en mente?". La ruta se decide con el siguiente mensaje.
- **Conversación en marcha:** se mantiene la intención anterior mientras el cliente siga con lo mismo. Si aparece una intención nueva, se vuelve a clasificar.
- **Información dentro de un evento** ("¿Y tiene parking?" mientras se le recomienda un espacio): se responde y se sigue con `nuevo_evento`. No cambia la ruta.
- **`reserva` frente a `nuevo_evento`:** si no hay espacio **y** fecha concretos, es `nuevo_evento`.
- **`cambio_reserva` frente a `reserva`:** "cambiar", "mover", "cancelar" o "mi reserva" sobre algo que ya existe → `cambio_reserva`.
- Si la validación del script descarta el espacio elegido (aforo, antelación u horario), se explica el motivo y se proponen las alternativas que dé el script.
- En una reserva, si falta la disposición, se pregunta antes de validar el espacio.

## 4. Varias intenciones en un mismo mensaje
`scripts/router.py` las ordena por esta prioridad:
1. `privacidad`
2. `queja`
3. `persona`
4. `cambio_reserva`
5. `reserva` / `nuevo_evento`
6. `informacion`
7. `fuera_tema`

Se responde primero a la más prioritaria y se retoma lo demás en el mismo mensaje: "Paso tu reclamación al equipo de atención, que te responde en 24 h laborables. Y sobre la nueva cena, ¿para cuántas personas sería?"
La `ruta` registrada es la de la intención más prioritaria.
Si persona va con otra intención, la ruta del tema es la de esa otra intención.
Con una queja y un evento nuevo: primero se reconoce la queja (quién responde y en qué plazo) y se hace una sola pregunta del evento. El contacto se pide una sola vez, en el mensaje siguiente, y sirve para los dos temas.

## 5. Si duda
- Si el mensaje encaja en dos intenciones que llevan a **acciones distintas**, se pregunta en vez de suponer, con opciones concretas: "¿Quieres organizar un evento nuevo o es sobre una reserva que ya tienes?"
- Si las dos llevan a lo mismo, no se pregunta.
- Si después de preguntar sigue sin estar claro, se trata como `persona` (`escalar_humano`, motivo `peticion_humano`).

## 6. Ejemplos
- "Hola" → saludo: aviso de IA + "¿Qué evento tenéis en mente?"
- "Queremos una cena de empresa para 120 en marzo" → `nuevo_evento`, ruta `lead`
- "¿Tenéis parking en el Fòrum?" → `informacion`
- "Quiero bloquear el Mirador el 14 de marzo" → `reserva`
- "Necesito cambiar la fecha de mi reserva" → `cambio_reserva`
- "Quiero quejarme de mi última cena y organizar otra" → `queja` primero, después `nuevo_evento`; ruta `incidencia`
- "Tengo una pregunta sobre una reserva" → duda entre `cambio_reserva` e `informacion` → se pregunta
- "¿Qué tiempo hará mañana?" → `fuera_tema`
