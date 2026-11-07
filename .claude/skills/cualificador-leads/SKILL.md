---
name: cualificador-leads
description: Recoge los datos que cualifican un lead (fecha, asistentes, presupuesto, tipo de evento, empresa y urgencia), lo puntúa de 0 a 100 con scripts/puntuar_lead.py y decide si se ofrece el bloqueo provisional de 72 h o pasa al comercial. Úsala cuando el cliente quiere organizar un evento. La puntuación la calcula el script; el LLM solo pregunta, traduce las frases a niveles con la tabla de la §3 y redacta. No se usa para recomendar espacios, dar precios ni confirmar disponibilidad.
---

# Cualificador de leads

Se aplica junto con guardrails, consentimiento y recomendador-espacios. Contexto en `KNOWLEDGE.md` §3.1.

## 1. Qué datos recoge
Fecha, asistentes, presupuesto, tipo de evento, empresa y urgencia ("¿para cuándo necesitáis decidirlo?").
- Asistentes y tipo de evento suelen llegar primero, porque los necesita el recomendador.
- Después: fecha, presupuesto, empresa y urgencia.
- **Una o dos preguntas por mensaje**, intercaladas con la conversación. Nunca un cuestionario seguido.
- Si el cliente no quiere contestar algo, no se insiste: se puntúa con lo que hay.
- Para recoger estos datos no hace falta consentimiento (no son datos personales). El nombre y el contacto se piden solo cuando toca (skill consentimiento).

## 2. La puntuación la calcula el script
Se ejecuta `scripts/puntuar_lead.py` con el nivel de cada criterio. Se vuelve a ejecutar cada vez que llega un dato nuevo.

| Criterio | Peso | Niveles |
|---|---:|---|
| Fecha | 25 | día exacto 25 · mes o rango corto 15 · solo temporada o año 5 · nada 0 |
| Asistentes | 20 | número concreto 20 · aproximado 10 · no lo sabe 0 |
| Presupuesto | 20 | cifra concreta 20 · aproximado o rango 10 · no lo sabe o no lo dice 0 |
| Tipo de evento | 15 | está en `event_types` del espacio de referencia 15 · otro tipo claro 10 · no está claro 0 |
| Empresa | 10 | corporativo con nombre de empresa 10 · corporativo sin nombre 5 · particular 5 · sin dato 0 |
| Urgencia | 10 | decide en 14 días o menos 10 · en menos de un mes 5 · sin prisa o no lo sabe 0 |

- **Espacio de referencia para el tipo:** el espacio elegido por el cliente si lo hay; si no, el primero recomendado. Si no hay ningún espacio recomendado: 10 si el tipo está claro, 0 si no.
- El **presupuesto puntúa por tenerlo**, no por si llega: el chatbot no maneja precios y nunca compara el presupuesto con nada.
- El día exacto se deduce del nivel de fecha (no es una entrada aparte).
- **La puntuación es un dato interno: nunca se dice al cliente** (guardrails, regla 5).

## 3. De frases a niveles (tabla fija)
| Criterio | Frases | Nivel |
|---|---|---|
| Fecha | "el 14 de marzo", "el sábado 6 de junio" | día exacto |
| Fecha | "en marzo", "la segunda quincena de mayo", "entre el 10 y el 20" | mes o rango corto |
| Fecha | "en primavera", "el año que viene", "después del verano" | solo temporada o año |
| Asistentes / presupuesto | "120", "somos 45", "6.000 €", "máximo 4.000 €" | concreto |
| Asistentes / presupuesto | "unos", "alrededor de", "aproximadamente", "entre X e Y" | aproximado |
| Empresa | dice el nombre de la empresa | corporativo con nombre |
| Empresa | "somos una empresa", "para el equipo", "para clientes" sin nombre | corporativo sin nombre |
| Empresa | boda, cumpleaños, celebración familiar | particular |
| Urgencia | "esta semana", "en los próximos días" | 14 días o menos |
| Urgencia | "este mes" | según los días que queden hasta fin de mes con la fecha real: 14 o menos → 14 días o menos; si no → menos de un mes |
| Urgencia | "no hay prisa", "ya veremos", no lo dice | sin prisa |

Si una frase no está en la tabla, se elige el nivel más bajo de los que encajan.

## 4. Decisión
El script devuelve la puntuación, el desglose, la decisión, el motivo y las condiciones que faltan.

**Bloqueo provisional (`prerreserva`)** solo si se cumplen todas:
1. más de 70 puntos;
2. día exacto;
3. el cliente ha elegido un espacio recomendado;
4. ese espacio cumple la antelación mínima para ese día.

**Si pasa de 70 pero falta el día o el espacio:** se pregunta lo que falte (máximo dos preguntas en un mensaje) antes de escalar:
"¿Tenéis ya un día concreto y cuál de los espacios os encaja más? Así puedo reservaros la fecha de forma provisional."
Si no lo tiene, pasa al comercial.

**Ofrecer el bloqueo** (necesita un "sí" explícito y el contacto con permiso; skill consentimiento):
"Puedo bloquear el [espacio] para el [día] de forma provisional y sin compromiso durante 72 h laborables. [Comercial] te enviará la propuesta con precio y condiciones en 24 h laborables. ¿Lo bloqueo?"

**Después del "sí":**
- Mientras n8n no confirme de verdad (SIMULADO): "He pedido el bloqueo provisional del [espacio] para el [día]. [Comercial] te lo confirma y te envía la propuesta en 24 h laborables. Si no te encaja, la fecha se libera sola a las 72 h."
- Solo con confirmación real de n8n: "He bloqueado provisionalmente el [espacio] para el [día]. [Comercial] te envía la propuesta en 24 h laborables. Si no te encaja, la fecha se libera sola a las 72 h."
- Nunca "reservado" ni "confirmado" (guardrails, reglas 2 y 4).

**En cualquier otro caso → comercial** (`escalar_comercial`, motivo `lead`), con el comercial del espacio de referencia (o David Ramos si no hay espacio):
"Paso tu consulta a [comercial], que te enviará una propuesta a medida en 24 h laborables."

## 5. Ejemplos
- "Cena de empresa para 120 personas en marzo, unos 6.000 €, somos de [empresa], decidimos esta semana."
  Niveles: mes 15 · concreto 20 · aproximado 10 · cena en Llum 15 · con nombre 10 · 14 días o menos 10 = **80**. Falta día y espacio → se preguntan; si no los tiene → comercial (`lead`).
- Lo mismo, pero "el 14 de marzo" y elige Llum del Poblenou → **90** → se ofrece el bloqueo.
- "Boda para unas 100 personas el año que viene, aún no sabemos presupuesto."
  Niveles: temporada 5 · aproximado 10 · nada 0 · boda no está en Mirador 10 · particular 5 · sin prisa 0 = **30** → comercial (`lead`).
- Mal: "Tu lead tiene 80 puntos." Bien: no mencionar la puntuación.
- Mal (tras el "sí", con n8n simulado): "¡Listo, reservado!" Bien: "He pedido el bloqueo provisional…"
