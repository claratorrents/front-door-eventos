# Prueba cualificador 02

Fecha: 7 de noviembre de 2026
Skill: `.claude/skills/cualificador-leads/SKILL.md` versión 2 (md5 `6bbd333fe88fcd5b391b4fcbff2998d2`, comprobado), junto con guardrails, consentimiento y recomendador-espacios.
Scripts: `scripts/puntuar_lead.py` (`test_puntuar_lead.py`: 10/10) y `scripts/recomendar.py` (`test_recomendar.py`: 11/11).
Método: igual que la prueba 01. Se repite la cena de 120 (primero sin día y después con "el 14 de marzo") y se comprueba la frase tras el "sí". **[aviso de IA]** abrevia el aviso. Los datos del cliente aparecen como `[empresa]`, `[nombre]` y `[email]`. La puntuación solo aparece en la columna interna.

## Cena de 120

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Cena de empresa para 120 personas en marzo, unos 6.000 €, somos de [empresa], decidimos esta semana. | Niveles (tabla §3): "en marzo" → mes; "120" → concreto; "unos 6.000 €" → **aproximado**; dice el nombre → corporativo con nombre; "esta semana" → 14 días o menos |
| B1 | [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? ¿Y hasta qué hora más o menos? | Cena → se pregunta la hora antes de recomendar |
| C2 | Banquete, sí. Hasta las 00:00. | |
| B2 | **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Encaja para una cena. *[foto: llum-poblenou-foto-01]*<br>**Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Encaja para una cena. El salón hasta las 03:00; la terraza cierra a las 23:30. Cabe justo; si podéis ser alguno más, mejor el Llum del Poblenou. *[foto: mirador-montjuic-foto-02]*<br>¿Tenéis ya un día concreto y cuál de los espacios os encaja más? Así puedo reservaros la fecha de forma provisional. | `recomendar 120 banquet --hora-fin 00:00` → Llum, Mirador (aviso terraza).<br>`puntuar_lead`: mes 15 · concreto 20 · aproximado 10 · cena en Llum (primer recomendado) 15 · con nombre 10 · 14 días o menos 10 = **80** → `escalar_comercial`; faltan `dia_exacto`, `espacio_elegido`, `antelacion_cumplida`.<br>Pasa de 70 pero faltan el día y el espacio → se preguntan los dos con la frase de §4 |
| C3 | El 14 de marzo, y nos quedamos con el Llum. | "El 14 de marzo" → día exacto |
| B3 | Lo compruebo con el calendario y te digo enseguida. | Antelación: 127 días ≥ 7 → cumplida.<br>`puntuar_lead` (día exacto, elegido Llum, antelación) = **90** → `prerreserva`.<br>`consulta_disponibilidad` → n8n: libre (SIMULADO) |
| B4 | Según el calendario, ese día parece libre. Te lo confirma el comercial. Puedo bloquear el Llum del Poblenou para el 14 de marzo de forma provisional y sin compromiso durante 72 h laborables. En ese plazo, Marta Soler te envía la propuesta con precio y condiciones. ¿Lo bloqueo? | Frase de oferta de §4 |
| C4 | Sí. | "Sí" explícito |
| B5 | Para hacerlo necesito tu nombre y un email o teléfono (el que prefieras); la empresa ya me la has dicho. ¿Me das permiso para guardarlos solo para responder a esta consulta? | Consentimiento §3–§4 |
| C5 | Sí: [nombre], [email]. | Apunte `otorgado` (finalidad "responder a la consulta"; datos nombre, email, empresa) |
| B6 | **He pedido el bloqueo provisional del Llum del Poblenou para el 14 de marzo. Marta Soler te lo confirma y te envía la propuesta en 24 h laborables. Si no te encaja, la fecha se libera sola a las 72 h.** Una última cosa: ¿quieres recibir novedades de espacios y eventos? Es opcional. | `decision: prerreserva`. Frase de §4 "Después del sí" para n8n SIMULADO (ni "reservado" ni "confirmado"). Publicidad, una vez, justo después de la acción principal |

**Rama sin día** (si en C3 dice "aún no tenemos día"): "Paso tu consulta a Marta Soler, que te enviará una propuesta a medida en 24 h laborables." Después se pide el contacto con permiso (`escalar_comercial`, `lead`, comercial del espacio de referencia: Llum).

**¿Cumple?** Sí.
- **Puntuación:** da los 80 y 90 que recalculasteis, con "unos 6.000 €" como aproximado.
- **Día y espacio:** se preguntan juntos en un mensaje.
- **Bloqueo:** se ofrece solo cuando se cumplen las 4 condiciones, después de comprobar la disponibilidad.
- **Tras el "sí":** se usa la frase fija para n8n simulado. No dice "reservado", "confirmado" ni "bloqueado".
- **Puntuación interna:** no aparece en ninguna respuesta.

## Comentarios (no hacen fallar la prueba)

1. **Dos plazos para la propuesta:** la oferta dice "En ese plazo [72 h], Marta Soler te envía la propuesta" y la frase tras el "sí" dice "en 24 h laborables". No se contradicen (24 h cabe dentro de 72 h), pero el cliente lee dos plazos distintos en dos mensajes seguidos.
2. **Nombres de nivel en el script:** para que coincidan con la tabla de la skill, he renombrado niveles respecto a la versión 1: `concreto`/`aproximado` para presupuesto, `corporativo_con_nombre`/`corporativo_sin_nombre` y `14_dias_o_menos`/`menos_de_un_mes`. El tipo ya no se pasa como nivel: el script lo calcula con `--tipo-evento`, `--espacio-elegido` y `--primer-recomendado`.
3. **Test extra:** he añadido un caso que no pedisteis para comprobar la prioridad del espacio de referencia. En una conferencia con el Fòrum como primer recomendado y el Mirador elegido, el tipo vale 10, porque manda el elegido. Ninguno de vuestros casos lo cubría.
