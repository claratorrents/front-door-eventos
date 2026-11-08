# eventos-front-door

> Generado por `scripts/empaquetar_plugin.py`. No se edita a mano: los cambios se hacen en el proyecto y se vuelve a generar.

Plugin de Claude Code con las skills del chatbot "front door" de una empresa que alquila espacios para eventos (datos sintéticos, prototipo del máster en La Salle).

## Qué incluye
- **Skills:** router-intenciones, guardrails, consentimiento, recomendador-espacios, cualificador-leads y media-espacios.
- **Scripts de reglas fijas** (Python 3, sin dependencias): `recomendar.py` (recomendación, validación del espacio elegido y media aprobada), `puntuar_lead.py` (puntuación del lead), `router.py` (qué se hace con cada intención) y `validar_datos.py`.
- **Datos:** `data/espacios.json` (6 espacios) y `data/inventario.json`.
- **Media:** `media/placeholders/`, las fotos ilustrativas de los espacios (generadas con IA). `validar_datos.py` comprueba que cada foto aprobada tiene su archivo.
- **Contexto:** `KNOWLEDGE.md` (decisiones del equipo, que las skills citan) y `AGENTS.md` (las reglas del chatbot).

Las decisiones las toman los scripts; el LLM clasifica y redacta.

## Instalación
Desde Claude Code, con el repositorio del proyecto en tu ordenador:

```
/plugin marketplace add <ruta-al-repositorio>
/plugin install eventos-front-door@front-door-eventos
```

Las skills se usan con el prefijo del plugin, por ejemplo `/eventos-front-door:router-intenciones`.

## Importante
El chatbot necesita además las reglas de `AGENTS.md` (las 5 reglas que nunca se rompen). `AGENTS.md` ya viene dentro del plugin: basta con copiarlo al proyecto donde lo uses y crear un `CLAUDE.md` con `@AGENTS.md`.
