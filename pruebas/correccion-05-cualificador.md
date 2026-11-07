# Corrección 05 · Cualificador de leads

Fecha: 7 de noviembre de 2026
Archivos: `.claude/skills/cualificador-leads/SKILL.md`, `scripts/puntuar_lead.py`, `scripts/test_puntuar_lead.py`; también `KNOWLEDGE.md` (§3.1 y §5) y la skill de consentimiento (§2), ya ajustados en la ronda 1.
Pruebas: `pruebas/prueba-cualificador-01.md` (antes) y `pruebas/prueba-cualificador-02.md` (después)

## Antes

Primera versión de la skill, escrita por el equipo, con la puntuación en `scripts/puntuar_lead.py`. El script dio los 5 resultados calculados por el equipo (5/5) y las dos conversaciones de la prueba 01 (cena de 120 y boda) cumplieron. Pero la lectura detallada sacó criterios inestables y una frase que faltaba.

## Problema

| # | Qué falló o no convencía en la prueba 01 |
|---|---|
| 1 | No había frase para después del "sí" al bloqueo. Con n8n simulado, decir "bloqueado" sería presentar como confirmado algo SIMULADO. |
| 2 | "Unos" no puntuaba igual: "unos 6.000 €" contaba como cifra concreta (20) y "unas 100 personas" como aproximado (10). |
| 3 | "Si solo falta el día exacto, se pregunta": no decía qué hacer cuando faltaban el día y el espacio a la vez. |
| 4 | El tipo se puntuaba siempre con el primer espacio recomendado, aunque el cliente eligiera otro, y no había regla sin espacio. |
| 5 | Pasar frases a niveles lo decidía el LLM ("este mes", "empresa identificada"…). |
| 6 | El día exacto se pedía como entrada aparte, y podía contradecir el nivel de fecha. |

## Cambio (decidido por el equipo)

| # | Decisión | Dónde |
|---|---|---|
| 1 | Frases fijas tras el "sí": con n8n SIMULADO, "He pedido el bloqueo provisional… [Comercial] te lo confirma… se libera sola a las 72 h"; con confirmación real, "He bloqueado provisionalmente…". Nunca "reservado" ni "confirmado". | Skill §4 |
| 2 | "Unos", "alrededor de", "aproximadamente" y "entre X e Y" son **aproximado** (10) tanto en asistentes como en presupuesto. La cena pasa de 90 a 80, y de 100 a 90 con día y espacio. | Skill §2, §3 y §5; tests |
| 3 | Si pasa de 70 pero falta el día o el espacio, se pregunta lo que falte (máximo dos preguntas): "¿Tenéis ya un día concreto y cuál de los espacios os encaja más?…". Si no lo tiene, pasa al comercial. | Skill §4 |
| 4 | Espacio de referencia para el tipo: el elegido; si no, el primero recomendado; sin ninguno, 10 si el tipo está claro y 0 si no. El script lo calcula con `event_types`. | Skill §2, `puntuar_lead.py` |
| 5 | Tabla fija de frases a niveles. "Este mes" se calcula con la fecha real: si quedan 14 días o menos hasta fin de mes, es 14 días o menos (10); si no, menos de un mes (5). El script lo hace con `--urgencia este_mes`. Nuevo nivel "corporativo sin nombre" (5). | Skill §3, `puntuar_lead.py` |
| 6 | El día exacto se deduce del nivel de fecha. | Skill §2, `puntuar_lead.py` |

## Después

- `scripts/test_puntuar_lead.py`: **10/10**.
  - Los 5 casos del equipo: 80 y 90 recalculados; 30, 85 y 70 sin cambios.
  - Los 4 casos nuevos pedidos: boda sin espacio → tipo 10; empresa sin nombre → 5; "este mes" el día 20 → 10 y el día 5 → 5.
  - Un caso extra: el espacio elegido manda sobre el primero recomendado.
- `scripts/test_recomendar.py`: 11/11. Validador: todo correcto.
- Prueba 02 (cena de 120, sin día y con "el 14 de marzo"): cumple, con la frase fija tras el "sí" para n8n simulado.
- Queda abierto, sin hacer fallar la prueba: la oferta del bloqueo habla de 72 h y la frase tras el "sí" dice que la propuesta llega en 24 h laborables. El cliente ve dos plazos en dos mensajes seguidos.
