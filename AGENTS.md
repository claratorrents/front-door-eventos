# AGENTS.md · Front Door de eventos

Construimos un chatbot "front door" para una empresa que alquila espacios para eventos ([EMPRESA]): atiende al visitante de la web, entiende qué quiere y lo resuelve o lo pasa a la persona adecuada. Es un prototipo para el máster (La Salle) con revisión humana al final.

Claude Code construye lo que ve el usuario (chat y dashboard). n8n recibe la consulta por webhook al final de la conversación y hace el proceso por detrás: valida, asigna espacio y comercial, puntúa, envía al cliente el email con Calendly, avisa al comercial y lo registra (KNOWLEDGE.md §3.2). No hay calendario ni reservas en el chatbot. Mientras n8n no esté conectado, el envío se simula. Todo dato simulado se marca como SIMULADO en los datos internos, y al cliente nunca se le presenta como confirmado.

El contexto completo está en KNOWLEDGE.md.

## Las 5 reglas que nunca se rompen

1. **Solo datos sintéticos.** Nada de datos reales de personas ni claves de API en el chat o en el repo.
2. **Nunca dar precios, presupuestos ni disponibilidad:** el chatbot recoge necesidades y presupuesto; el precio y la fecha los confirma el comercial en la llamada.
3. **Decidir con reglas, redactar con el LLM.** El router clasifica con el LLM sobre una lista cerrada de intenciones; lo que se hace con cada una y las demás decisiones van por script o tabla fija. La puntuación oficial del lead es la de n8n.
4. **Consentimiento antes de guardar datos.** Aviso de IA primero; sin consentimiento, registro anónimo (sin nombre, email ni teléfono).
5. **Nunca descuentos; lo delicado va a una persona.** Descuentos, quejas, temas legales y excepciones se escalan a humano.

## Cómo quiero que trabajes conmigo

- Una tarea cada vez. Antes de cambios grandes, enséñame el plan y espera mi aprobación.
- No digas "hecho" sin ejecutar la comprobación y enseñarme el resultado.
- Commit solo tras un paso que funcione y cuando yo lo apruebe.
- No instales nada, no hagas push ni borres archivos sin preguntarme antes.
- No crees contenido del proyecto por tu cuenta (skills, catálogo, inventario, textos): lo escribimos nosotras y tú lo ejecutas, pruebas y guardas. Si falta un dato, pregunta; no lo inventes ni lo completes con ejemplos.
- Llévame la contraria si algo no tiene sentido; dime qué falta o dónde añade trabajo.
- No cambies los campos del contrato del webhook (KNOWLEDGE.md §3.2) sin avisarme.
- Escribe en español natural y claro, como lo haría el equipo. Al cliente, una o dos preguntas por mensaje y nunca rutas de archivo. Sin fórmulas típicas de IA ('sin duda', 'es importante destacar', 'en resumen'...).
- Documenta cada corrección en `pruebas/correccion-XX-<skill>.md` (antes / problema / cambio / después).
