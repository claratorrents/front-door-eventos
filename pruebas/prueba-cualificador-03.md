# Prueba cualificador 03

Fecha: 8 de noviembre de 2026
Skill: `.claude/skills/cualificador-leads/SKILL.md`, versión adaptada a la §3.2 (md5 `ac285e4f7172446cfae8d702ad34a9ee`, comprobado), junto con guardrails, recomendador-espacios y consentimiento versión 3.
Scripts: `scripts/datos_consulta.py` (`test_datos_consulta.py` 10/10), `scripts/router.py` y `scripts/recomendar.py`.
Método: simulación del chatbot por la ruta estrella (KNOWLEDGE §3.1): consulta → recomendación con fotos → elige espacio → datos → pregunta de privacidad. Se para en la pregunta de privacidad, sin envío. En cada turno se ejecuta `datos_consulta.py` con lo que se sabe y lo ya preguntado. Datos sintéticos.

## Conversación

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Cena de empresa para 120 personas en marzo. | `router.py nuevo_evento` → guardrails, recomendador, cualificador (+ media y consentimiento cuando toque) · ruta `lead`. Niveles: tipo "cena de empresa", asistentes "120", fecha **mes** |
| | | `datos_consulta.py --tipo "cena de empresa" --asistentes 120 --fecha mes` → faltan [espacio_o_zona, dia_exacto, presupuesto, necesidades] · preguntas [espacio_o_zona, dia_exacto] · listo **false** |
| B1 | [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? ¿Y hasta qué hora más o menos? | El recomendador necesita la hora de fin antes de recomendar (cena). El espacio sale de las tarjetas, así que las preguntas del cualificador esperan al mensaje siguiente |
| C2 | Sí, banquete, hasta las 00:00. | Disposición `banquet`, hora de fin 00:00 |
| B2 | **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Encaja para una cena de empresa. *[imagen: llum-poblenou-foto-01, Imagen ilustrativa]*<br>**Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Encaja para una cena de empresa. El salón hasta las 03:00; la terraza cierra a las 23:30. Cabe justo; si podéis ser alguno más, mejor el Llum. *[imagen: mirador-montjuic-foto-02, Imagen ilustrativa]*<br>¿Cuál os encaja más? ¿Tenéis ya un día concreto? | `recomendar.py --asistentes 120 --disposicion banquet --hora-fin 00:00` → Llum `comodo` (foto-01), Mirador `al_limite` (foto-02, terraza hasta las 23:30). Sin `--dias` porque solo se sabe el mes.<br>Preguntas = las dos de `datos_consulta.py`: espacio_o_zona y dia_exacto |
| C3 | El Llum. El día aún no lo sabemos. | Espacio: "Llum del Poblenou". Día exacto: no lo sabe → **cuenta como preguntado** (§4) |
| | | `datos_consulta.py … --espacio "Llum del Poblenou" --fecha mes --preguntados espacio_o_zona,dia_exacto` → faltan [presupuesto, necesidades] · preguntas [presupuesto, necesidades] · listo **false** |
| B3 | Perfecto. ¿Tenéis un presupuesto aproximado? ¿Y necesitaréis algo especial, como catering o audiovisuales? | Las dos preguntas del script, en un mensaje |
| C4 | Unos 6.000 €. Necesitamos pantalla y sonido. ¿Nos podéis hacer un 10 % de descuento? | Presupuesto "unos 6.000 €" (dado: n8n acepta rangos y aproximados). Necesidades "pantalla y sonido". Descuento → §5: se apunta para `message`, no se escala aparte |
| | | `datos_consulta.py … --presupuesto "unos 6.000 €" --necesidades "pantalla y sonido" --preguntados espacio_o_zona,dia_exacto,presupuesto,necesidades` → faltan [] · preguntas [] · listo **true** → consentimiento §4 |
| B4 | El descuento lo verás con el comercial en la llamada. Para que el equipo te envíe la propuesta necesito tu nombre y tu email. ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad? | Frase de §5 del cualificador + pregunta de privacidad de consentimiento §4, con su texto fijo. **Fin de la prueba** |

## Lo que iría en el envío (si acepta)

| Campo | Valor |
|---|---|
| `preferred_location` | Llum del Poblenou |
| `event_type` | cena de empresa |
| `event_date` | `""` (solo dijo el mes; n8n lo lee de la conversación) |
| `guests` | 120 |
| `budget_eur` | unos 6.000 € |
| `message` | Cena hasta las 00:00, en banquete. Necesitan pantalla y sonido. Pide un 10 % de descuento. |

## ¿Cumple?

**Sí.**
- **Orden y preguntas:** los datos se piden en el orden de la §2, con las preguntas que da el script y nunca más de dos por mensaje.
- **Una sola vez:** el día exacto se pregunta una vez y, con "aún no lo sabemos", no se vuelve a preguntar (§4).
- **Sin puntuación:** no aparece en ningún momento. El script no la calcula y no se dice nada parecido al cliente.
- **Descuento:** no se concede ni se escala aparte; va a `message` y se dice "Lo verás con el comercial en la llamada" (§5).
- **Paso a consentimiento:** con `listo_para_enviar` verdadero se pasa a la pregunta de privacidad de consentimiento §4. La empresa, el nombre y el email no los pide el cualificador.
- **Sin disponibilidad ni precio:** no se ofrece bloqueo ni se habla de disponibilidad o de precio.

## Comentarios

1. **Quién pregunta primero, el recomendador o el cualificador.** En B1, el script decía preguntar espacio y día, pero el recomendador necesita antes la hora de fin (cena) para poder recomendar, y el espacio sale de sus tarjetas. He dado prioridad al recomendador. Ninguna skill dice cómo se combinan las preguntas de las dos.
2. **Pregunta final de las tarjetas.** El recomendador (§3) cierra con una sola pregunta, por ejemplo "¿Queréis ver el plano o el recorrido 360°?". El cualificador pide "¿Cuál os encaja más?" después de las tarjetas, y el script añade el día exacto. En B2 he usado las dos del cualificador. Es para el punto 6 (recomendador).
3. **Frase del descuento.** Guardrails sigue diciendo "Los descuentos los valora el equipo comercial y te responden en 24 h laborables", que choca con la §5 del cualificador. Es para el punto 5 (guardrails).
4. **Fecha sin día exacto y antelación.** Con solo "marzo" el recomendador no comprueba la antelación (`--dias`). No afecta aquí (Llum necesita 7 días), pero un evento "este mes" podría quedar sin esa comprobación.
