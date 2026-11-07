---
name: media-espacios
description: Elige y presenta el material visual aprobado de un espacio (fotos, plano y recorrido 360°): la foto de la tarjeta de recomendación y lo que el cliente pida después. Úsala cuando el recomendador presenta un espacio o el cliente pide fotos, plano, vídeo o recorrido virtual. No se usa para recomendar espacios ni para dar precios o disponibilidad.
---

# Media de espacios

Se aplica junto con guardrails y recomendador-espacios. Datos en `data/espacios.json` (campo `media` de cada espacio); contexto en `KNOWLEDGE.md` §3.1.

## 1. Solo material aprobado
- Solo se enseña material con `approved: true`. Nunca la foto 2 del Jardí de Gràcia (patio antes de la reforma, no aprobada).
- Si un archivo no está aprobado, no existe para el cliente: no se menciona ni se dice que "está pendiente".

## 2. La foto de la tarjeta (con el recomendador)
- Una sola foto por espacio.
- Se elige la foto aprobada cuya `disposition` coincide con la disposición del evento.
- Si no hay ninguna que coincida, la primera foto aprobada del espacio.
- Nunca una foto de una zona que cierra antes del fin del evento. Si no hay foto con la misma disposición, mejor una de interior que una de una zona exterior.
- La elección sigue esta regla; el LLM no la cambia por intuición.

## 3. Lo que el cliente pide después
- **"¿Tenéis más fotos?"** → todas las fotos aprobadas del espacio, con su `description` como pie de foto.
- **Plano** → el plano aprobado, con su `description`.
- **Recorrido virtual / tour 360°** → el tour aprobado.
- Las fotos adicionales, el plano y el tour se piden al script; el LLM no los busca en los datos.
- Al final de la recomendación se puede ofrecer: "¿Queréis ver el plano o el recorrido 360° de alguno?" (una sola pregunta).

## 4. Lo que no hay
- **Vídeo:** no hay vídeos de ningún espacio. "No tenemos vídeo de este espacio, pero sí un recorrido virtual 360°. ¿Te lo enseño?"
- **Algo concreto que no aparece** (por ejemplo, "fotos del patio de noche"): se dice que no lo tenemos y se ofrece lo que sí hay. "No tenemos fotos del patio de noche; tengo esta del patio con las guirnaldas encendidas. ¿Te sirve?"
- **Nunca** se describe una foto que no existe ni se inventa cómo es un espacio más allá de su `description` y `full_profile` (guardrails, regla 7).

## 5. Cómo se presenta
- Siempre como imagen o enlace. **Nunca la ruta del archivo.**
- Pie de foto: la `description` del archivo, tal cual.
- Si el elemento tiene illustrative: true, el pie lo indica: "Imagen ilustrativa".

## 6. Ejemplos
- Cena para 120 → tarjeta de Llum del Poblenou con la foto de `disposition: banquet` ("Nave industrial montada para cena de gala, con luz cenital").
- Conferencia para 150 → tarjeta de Llum con la foto de `disposition: theater` ("Montaje de teatro frente a la pantalla de 4x3 m").
- Cóctel en el Jardí → la foto 1 (patio con guirnaldas). Mal: enseñar la foto 2, aunque el cliente pida "todas las fotos".
- "¿Tenéis vídeo de la Nau?" → "No tenemos vídeo de este espacio, pero sí un recorrido virtual 360°. ¿Te lo enseño?"
- Mal: "Aquí tienes la foto: /media/placeholders/nau-besos/foto-01.jpg".
