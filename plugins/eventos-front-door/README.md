# eventos-front-door

> Generado por `scripts/empaquetar_plugin.py`. No se edita a mano: los cambios se hacen en el proyecto y se vuelve a generar.

Plugin de Claude Code con las skills del chatbot "front door" de una empresa que alquila espacios para eventos (datos sintéticos, prototipo del máster en La Salle).

## Qué incluye
- **Skills:** router-intenciones, guardrails, consentimiento, recomendador-espacios, cualificador-leads, media-espacios y envio-n8n.
- **Scripts de reglas fijas** (Python 3, sin dependencias): `recomendar.py` (recomendación, validación del espacio elegido y media aprobada), `datos_consulta.py` (qué datos faltan en la consulta y qué preguntar), `router.py` (qué se hace con cada intención), `enviar_n8n.py` (envío de la consulta a n8n y registro anónimo) y `validar_datos.py`.
- **Datos:** `data/espacios.json` (6 espacios) y `data/inventario.json`.
- **Media:** `media/placeholders/`, las fotos ilustrativas de los espacios (generadas con IA). `validar_datos.py` comprueba que cada foto aprobada tiene su archivo.
- **Contexto:** `KNOWLEDGE.md` (decisiones del equipo, que las skills citan) y `AGENTS.md` (las reglas del chatbot).

Las decisiones las toman los scripts; el LLM clasifica y redacta.

## Envío a n8n
Al final de una consulta de evento, la skill envio-n8n llama a `scripts/enviar_n8n.py`, que envía la consulta al flujo de n8n una sola vez (POST con los 15 campos del contrato de `KNOWLEDGE.md` §3.2) y apunta cada conversación en un registro anónimo, `registros/conversaciones.jsonl`, sin nombre, email, teléfono, empresa ni texto de la conversación.

- **La URL y la clave solo van en variables de entorno:** `N8N_WEBHOOK_URL` y `N8N_API_KEY`. Nunca en el código, en el repositorio, en el chat ni en el navegador. El plugin no incluye ninguna.
- **Sin esas variables, el envío se simula:** el script no envía nada y responde `202_simulada`, con el mismo formato que un envío real. Así se puede probar el chatbot sin conectar n8n.
- Sin consentimiento, los datos personales no se envían y se tapan en la conversación; tarjetas, IBAN y DNI se tapan siempre.
- El registro se crea en `registros/` de la carpeta desde la que se ejecuta el chat (directorio de trabajo), nunca dentro de la carpeta del plugin.

## Instalación
Desde Claude Code, con el repositorio del proyecto en tu ordenador:

```
/plugin marketplace add <ruta-al-repositorio>
/plugin install eventos-front-door@front-door-eventos
```

Las skills se usan con el prefijo del plugin, por ejemplo `/eventos-front-door:router-intenciones`.

## Importante
El chatbot necesita además las reglas de `AGENTS.md` (las 5 reglas que nunca se rompen). `AGENTS.md` ya viene dentro del plugin: basta con copiarlo al proyecto donde lo uses y crear un `CLAUDE.md` con `@AGENTS.md`.
