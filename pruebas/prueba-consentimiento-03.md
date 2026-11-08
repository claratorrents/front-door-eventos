# Prueba consentimiento 03

Fecha: 8 de noviembre de 2026
Skill: `.claude/skills/consentimiento/SKILL.md` versión 3 (md5 `8e3e9d1a43b5524995b327ea2a697cfe`, comprobado), adaptada a `KNOWLEDGE.md` §3.2, junto con guardrails. Las recomendaciones salen de `scripts/recomendar.py`.
Método: simulación del chatbot (C = cliente, B = chatbot). Para cada caso, lo que se enviaría a n8n con el contrato de la §3.2. El envío es **SIMULADO** (respuesta 202 SIMULADA): todavía no hay URL ni clave.
Datos: todos sintéticos (`*.example`, "Demo Corp"). `lead_id` y `timestamp`: generados con la hora real del sistema al hacer la prueba (`2026-11-08T19:52:32Z`).
Fuera de esta prueba: el cualificador y el router todavía no están adaptados a la §3.2, así que aquí solo se recogen los datos que hacen falta para probar el consentimiento.

## Arranque común (casos a, b, c, d y g)

> C1: Hola, queremos una cena de empresa para 120 personas el 14 de marzo.
> B1: [aviso de IA] Para una cena lo normal es formato banquete. ¿Hasta qué hora más o menos?
> C2: Hasta las 00:00.
> B2: *(`recomendar.py --asistentes 120 --disposicion banquet --dias 126 --hora-fin 00:00` → Llum del Poblenou `comodo`, Mirador de Montjuïc `al_limite`, con aviso de zona: terraza hasta las 23:30)*
> **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Encaja para una cena de empresa. *[imagen: llum-poblenou-foto-01, Imagen ilustrativa]*
> **Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Encaja para una cena de empresa. El salón hasta las 03:00; la terraza cierra a las 23:30. Cabe justo; si podéis ser alguno más, mejor el Llum. *[imagen: mirador-montjuic-foto-02, Imagen ilustrativa]*
> ¿Cuál os encaja más?
> C3: El Llum. Tenemos unos 6.000 € y somos de Demo Corp.
> B3: Para que el equipo te envíe la propuesta necesito tu nombre y tu email. ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad?

Hasta aquí no se ha pedido ningún dato personal (§2): se piden al final, con el permiso en el mismo mensaje y mencionando la política de privacidad (§4).

## a) Acepta la privacidad y la publicidad

> C4: Sí. Laura Martínez, laura@ejemplo.example
> B4: ¿Quieres recibir también novedades de espacios y eventos? Es opcional.
> C5: Sí.
> *(envío a n8n → 202 SIMULADA)*
> B5: Gracias. El equipo te escribirá por email en breve.

Envío:
```json
{"lead_id": "CB-20261108-195232-47f0", "timestamp": "2026-11-08T19:52:32Z",
 "name": "Laura Martínez", "email": "laura@ejemplo.example", "company": "Demo Corp", "phone": "",
 "preferred_location": "Llum del Poblenou", "event_type": "cena de empresa", "event_date": "2027-03-14",
 "guests": "120", "budget_eur": "unos 6.000 €", "message": "Cena de empresa hasta las 00:00.",
 "conversation": "Bot: Hola, soy el asistente virtual de [EMPRESA]…\nClient: Hola, queremos una cena de empresa para 120 personas el 14 de marzo.\n…\nClient: Sí.",
 "gdpr_consent": "yes", "marketing_consent": "yes"}
```
- **gdpr_consent:** yes · **marketing_consent:** yes · **nombre y email:** sí.
- **¿Cumple?** Sí. La publicidad se pregunta una sola vez, aparte y después del "sí" a la privacidad (§5). El consentimiento viaja en el envío (§6).

## b) Acepta la privacidad y no contesta a la publicidad

> C4: Sí. Laura Martínez, laura@ejemplo.example
> B4: ¿Quieres recibir también novedades de espacios y eventos? Es opcional.
> C5: ¿Y cuándo me escribiréis?
> *(no contesta a la publicidad → `marketing_consent: no`; envío a n8n → 202 SIMULADA)*
> B5: Gracias. El equipo te escribirá por email en breve.

Envío: igual que a), con `lead_id` `CB-20261108-195232-2013` y **`"marketing_consent": "no"`**.
- **gdpr_consent:** yes · **marketing_consent:** no · **nombre y email:** sí.
- **¿Cumple?** Sí. No contestar cuenta como "no" (§5) y no se vuelve a preguntar.
- **Pero:** aquí el cliente cambia de tema, y eso deja claro que no contesta. Si simplemente deja de escribir, la skill no dice cuánto se espera ni si se envía igual (ver comentario 2).

## c) Dice que no a la privacidad

> C4: No, prefiero no dar mis datos.
> B4: Sin problema. Si cambias de idea, me lo dices; también puedes escribir al equipo en atencion@empresa-eventos.example.
> *(envío a n8n sin datos personales → 202 SIMULADA. El chatbot no dice nada más: ver comentario 3)*

Envío:
```json
{"lead_id": "CB-20261108-195232-ff64", "timestamp": "2026-11-08T19:52:32Z",
 "name": "", "email": "", "company": "", "phone": "",
 "preferred_location": "Llum del Poblenou", "event_type": "cena de empresa", "event_date": "2027-03-14",
 "guests": "120", "budget_eur": "unos 6.000 €", "message": "Cena de empresa hasta las 00:00.",
 "conversation": "Bot: Hola, soy el asistente virtual de [EMPRESA]…\n…\nClient: El Llum. Tenemos unos 6.000 € y somos de Demo Corp.\n…\nClient: No, prefiero no dar mis datos.\n…",
 "gdpr_consent": "no", "marketing_consent": "no"}
```
- **gdpr_consent:** no · **marketing_consent:** no (no se pregunta, porque solo se pregunta después del "sí") · **nombre y email:** no.
- **¿Cumple?** Sí: se envía sin nombre, email, teléfono ni empresa (§4; por confirmar con Ale).
- **Pero:**
  - La empresa no va en `company`, pero sigue en `conversation` ("somos de Demo Corp"). Ver comentario 4.
  - En el flujo de Ale, una consulta con `gdpr_consent: no` se para en el paso de validación y queda registrada como rechazada, sin IA ni emails.

## d) Solo quiere dar teléfono

> C4: Acepto, pero no quiero dar el email. Llamadme al +34 600 000 099.
> B4: Sin email el equipo no puede enviarte la propuesta. Si prefieres, llámanos al +34 930 000 000.

Envío: **ninguno** (§4: sin email no se puede enviar).
- **gdpr_consent / marketing_consent:** no se envían · **nombre y email:** no.
- Registro anónimo del chat: consulta `lead`, enviada a n8n: no. El teléfono no se guarda.
- **¿Cumple?** Sí, con la skill tal como está.
- **Pero:** un cliente que acepta la privacidad y da un teléfono no queda en ningún sitio para el comercial, mientras que el que dice "no" a todo (caso c) sí se envía y queda contado. Ver comentario 5.

## e) Da su email al principio y pregunta el precio

> C1: Hola. Mi email es ana@ejemplo.example, ¿cuánto cuesta el Jardí de Gràcia?
> B1: [aviso de IA] El precio te lo prepara el comercial en una propuesta a medida. Antes de usar tu email te preguntaré si aceptas nuestra política de privacidad. ¿Cuántos asistentes seríais?
> C2: Unos 80, un cóctel de networking el 30 de diciembre, hasta las 22:00.
> B2: *(`recomendar.py --asistentes 80 --disposicion cocktail --dias 52 --hora-fin 22:00` → Jardí de Gràcia `comodo`)*
> **Jardí de Gràcia.** Oasis botánico y patio íntimo entre callejuelas históricas. Hasta 110 personas en cóctel. Encaja para un cóctel de networking. *[imagen: jardi-gracia-foto-01, Imagen ilustrativa]* ¿Os encaja?
> C3: Sí, perfecto.
> B3: Para que el equipo te envíe la propuesta necesito tu nombre; el email ya me lo has dado. ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad?
> C4: Sí, Ana Soto.
> B4: ¿Quieres recibir también novedades de espacios y eventos? Es opcional.
> C5: No, gracias.
> *(envío a n8n → 202 SIMULADA)*
> B5: Gracias. El equipo te escribirá por email en breve.

Envío:
```json
{"lead_id": "CB-20261108-195232-39eb", "timestamp": "2026-11-08T19:52:32Z",
 "name": "Ana Soto", "email": "ana@ejemplo.example", "company": "", "phone": "",
 "preferred_location": "Jardí de Gràcia", "event_type": "cóctel de networking", "event_date": "2026-12-30",
 "guests": "unos 80", "budget_eur": "", "message": "Cóctel de networking hasta las 22:00.",
 "conversation": "Bot: Hola, soy el asistente virtual de [EMPRESA]…\nClient: Hola. Mi email es ana@ejemplo.example, ¿cuánto cuesta el Jardí de Gràcia?\n…\nClient: No, gracias.",
 "gdpr_consent": "yes", "marketing_consent": "no"}
```
- **gdpr_consent:** yes · **marketing_consent:** no · **nombre y email:** sí.
- **¿Cumple?** Sí:
  - El email no se usa hasta el "sí" a la privacidad (§4).
  - El precio no se da (guardrails, regla 1) y la conversación sigue con una pregunta.
  - El email puede ir en `conversation` porque al final hay consentimiento.
- **Pero:** la frase fija de §4 pide "tu nombre y tu email". Como el email ya estaba, la he adaptado ("el email ya me lo has dado"). La skill no prevé este caso.

## f) "Borrad mis datos" sin consulta en marcha

> C1: Hola, borrad mis datos.
> B1: [aviso de IA] Para eso escribe al equipo en atencion@empresa-eventos.example o llama al +34 930 000 000 (de lunes a sábado, de 9 a 18 h). Ellos lo gestionan.

Envío: **ninguno** (privacidad no va a n8n, §3.2 decisión 5).
- **gdpr_consent / marketing_consent:** no se envían · **nombre y email:** no se piden (§8: nada de "localizar").
- `router.py privacidad` → skills guardrails y consentimiento, sin decisión, ruta `privacidad`: cuadra con la skill.
- **¿Cumple?** Sí. Sin plazos y sin pedir datos.

## g) Acepta y, antes del envío, dice "mejor no uséis mi email"

> C4: Sí. Laura Martínez, laura@ejemplo.example
> B4: ¿Quieres recibir también novedades de espacios y eventos? Es opcional.
> C5: Sí. Bueno, pensándolo mejor, mejor no uséis mi email.
> B5: Hecho, no lo usaremos.
> *(se envía como si hubiera dicho que no a la privacidad (§8 → §4) → 202 SIMULADA)*

Envío:
```json
{"lead_id": "CB-20261108-195232-e645", "timestamp": "2026-11-08T19:52:32Z",
 "name": "", "email": "", "company": "", "phone": "",
 "preferred_location": "Llum del Poblenou", "event_type": "cena de empresa", "event_date": "2027-03-14",
 "guests": "120", "budget_eur": "unos 6.000 €", "message": "Cena de empresa hasta las 00:00.",
 "conversation": "…\nClient: Sí. [nombre tapado], [email tapado]\n…\nClient: Sí. Bueno, pensándolo mejor, mejor no uséis mi email.\nBot: Hecho, no lo usaremos.",
 "gdpr_consent": "no", "marketing_consent": "no"}
```
- **gdpr_consent:** no · **marketing_consent:** no · **nombre y email:** no.
- **¿Cumple?** Sí: se cumple al momento y se envía como un "no" (§8).
- **Pero:**
  - El cliente dijo "sí" a la publicidad y después retiró el email. He enviado `marketing_consent: no` porque sin email no hay a dónde mandar novedades, pero la skill no lo dice.
  - Solo retiró el email, y la skill quita también el nombre.
  - En `conversation` he tapado nombre y email. Para el email se sigue el Pendiente de §3.1 ("tapar… email y teléfono si no hay permiso"); el nombre y la empresa no están cubiertos (comentario 4).

## Registro anónimo del chat (`registros/conversaciones.jsonl`, decisión 11)

| Caso | intención | ruta | enviado a n8n | consentimiento |
|---|---|---|---|---|
| a | nuevo_evento | lead | sí | sí |
| b | nuevo_evento | lead | sí | sí |
| c | nuevo_evento | lead | sí | no |
| d | nuevo_evento | lead | no | sí (sin envío) |
| e | informacion → nuevo_evento | lead | sí | sí |
| f | privacidad | privacidad | no | — |
| g | nuevo_evento | lead | sí | no (retirado) |

Los nombres de los campos son provisionales: la decisión 11 dice qué se guarda (intención, ruta, resuelto sí/no, enviado a n8n sí/no) y la skill añade el consentimiento (§6). **"Resuelto" no lo he rellenado:** no está definido qué cuenta como resuelto (¿una consulta enviada a n8n?, ¿un "borrad mis datos" con el contacto del equipo?).

**Resultado:** los 7 casos cumplen la skill versión 3. Quedan los puntos de abajo, que la skill no resuelve.

## Comentarios

1. **`marketing_consent` cuando no hay "sí" a la privacidad** (casos c y g): el contrato exige el campo y la skill solo pregunta la publicidad después del "sí". He enviado `no`; convendría escribirlo en la skill.
2. **Publicidad sin respuesta porque el cliente se va** (caso b): ¿cuánto se espera antes de enviar, y se envía igual? Encaja mejor en la skill de envío a n8n.
3. **Qué dice el chatbot con el 202 si el cliente dijo "no"** (casos c y g): la §3.2 dice que con 202 se responde "Gracias. El equipo te escribirá por email en breve.", pero sin email eso es falso. Aquí el chatbot no dice nada más.
4. **Qué se tapa en `conversation` sin consentimiento:** el Pendiente de §3.1 cubre email y teléfono. Pero el nombre y la empresa también llegan en la conversación, y la skill no lo dice.
5. **Solo teléfono (caso d) frente a "no" (caso c):** el que acepta y da un teléfono no llega a nadie; el que lo rechaza todo se envía. ¿Debería enviarse al menos como consulta sin datos personales (igual que el "no"), o anotarse de otra forma?
