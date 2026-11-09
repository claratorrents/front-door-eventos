# Front door de eventos

Chatbot "front door" para una empresa que alquila espacios para eventos (prototipo del máster de La Salle, con datos sintéticos).
Atiende al visitante, recomienda espacios con fotos y planos, recoge la consulta con consentimiento y la envía a n8n.
Las decisiones las toman scripts de reglas (`scripts/`); las reglas del chatbot están en las skills (`.claude/skills/`).
Arrancar el chat (Python 3, sin instalar nada): `python3 chat/servidor.py` y abrir `127.0.0.1:8000`.
Sin `N8N_WEBHOOK_URL` y `N8N_API_KEY`, el envío a n8n es simulado.

- Para entender el proyecto en 5 minutos (profesor): [docs/LEEME_PROFESOR.md](docs/LEEME_PROFESOR.md).
- Para usar `chat/` como backend de otro front: [docs/INTEGRACION.md](docs/INTEGRACION.md).
- Contexto y decisiones del proyecto: [KNOWLEDGE.md](KNOWLEDGE.md) · reglas: [AGENTS.md](AGENTS.md).
