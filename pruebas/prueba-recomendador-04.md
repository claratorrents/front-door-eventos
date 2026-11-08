# Prueba recomendador 04

Fecha: 8 de noviembre de 2026 (los días hasta el evento se cuentan desde hoy)
Skill: `.claude/skills/recomendador-espacios/SKILL.md`, versión adaptada a la §3.2 (md5 `838289137819ee507535d2ebd77a9072`, comprobado), con router, cualificador, guardrails y media.
Scripts:
- `scripts/recomendar.py`, con `--validar` que ahora devuelve `avisos_zona` (`test_recomendar.py` 25/25);
- `scripts/datos_consulta.py`;
- `scripts/router.py` (`nuevo_evento` en los 4 casos).

Método: simulación del chatbot (C = cliente, B = chatbot). Cada conversación empieza con **[aviso de IA]**. Datos sintéticos; no se llega a enviar nada.

## 1. "Cena de empresa para 120 personas en marzo", hasta que elige espacio

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Cena de empresa para 120 personas en marzo. | `datos_consulta.py --tipo "cena de empresa" --asistentes 120 --fecha mes` → preguntas [espacio_o_zona, dia_exacto] |
| B1 | [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja? ¿Y hasta qué hora más o menos? | §1: una cena suele acabar tarde, así que se pregunta la hora antes de recomendar |
| C2 | Sí, hasta las 00:00. | |
| B2 | **Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 150 personas en banquete. Encaja para una cena de empresa. *[imagen: llum-poblenou-foto-01, Imagen ilustrativa]*<br>**Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Hasta 120 personas en banquete. Encaja para una cena de empresa. El salón hasta las 03:00; la terraza cierra a las 23:30. Cabe justo; si podéis ser alguno más, mejor el Llum. *[imagen: mirador-montjuic-foto-02, Imagen ilustrativa]*<br>¿Cuál os encaja más? También puedo enseñaros el plano o el recorrido 360°. ¿Tenéis ya un día concreto? | `recomendar.py --asistentes 120 --disposicion banquet --hora-fin 00:00` → Llum `comodo`, Mirador `al_limite` con `avisos_zona` terraza 23:30.<br>**Pregunta final nueva (§3):** una sola que junta la elección y el plano o 360°; la segunda pregunta es el día exacto del cualificador |
| C3 | El Llum. El día aún no lo sabemos. | Elección → **`preferred_location`: "Llum del Poblenou"** (§3, decisión 2). Desde aquí se puede nombrar a Marta Soler (guardrails) |
| | | `datos_consulta.py … --espacio "Llum del Poblenou" --fecha mes --preguntados espacio_o_zona,dia_exacto` → preguntas [presupuesto, necesidades]. Sigue el cualificador |

- **¿Cumple?** **Sí.**
  - La pregunta final es la nueva y junta la elección con el plano o el 360°.
  - El espacio elegido pasa a `preferred_location`.
  - Sin precio ni porcentajes, y el aviso de la terraza sale del script.

## 2. "Somos 500 para un cóctel"

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Somos 500 para un cóctel. | `recomendar.py --asistentes 500 --disposicion cocktail` → **ningún espacio** (el mayor, la Nau, tiene 400 en cóctel) |
| B1 | [aviso de IA] Ninguno de nuestros espacios tiene sitio para 500 personas en cóctel. Si quieres, sigo con tu consulta y la paso al equipo para que vea qué opciones hay. | §5, por aforo. → `escalar_comercial`, `excepcion` · al message: "Ningún espacio tiene aforo para 500 en cóctel". Sin nombre de comercial y sin plazos |
| C2 | Sí, adelante. | `datos_consulta.py --tipo cóctel --asistentes 500` → preguntas [espacio_o_zona, fecha] |
| B2 | ¿Tenéis alguna zona de Barcelona en mente? ¿Y para qué fecha sería? | Sin espacio, basta con la zona (cualificador §2). La consulta sigue su camino normal hasta el envío |

- **¿Cumple?** **Sí.**
  - Sin espacio, la consulta sigue y lo que no se resuelve va al message.
  - `preferred_location` será la zona que diga, o `""`.
  - En el flujo de Ale, una consulta con más asistentes que cualquier espacio no recibe el email automático y el equipo recibe el aviso para contactar: cuadra con no prometer nada.

## 3. Elige el Mirador sin día y después dice "el 20 de noviembre"

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Cena de empresa para 100 en noviembre, hasta las 00:00. | `recomendar.py --asistentes 100 --disposicion banquet --hora-fin 00:00` (sin `--dias`: solo se sabe el mes) → Mirador `comodo` (terraza 23:30), Llum `comodo` |
| B1 | [aviso de IA] Para una cena lo normal es formato banquete; ¿os encaja?<br>**Mirador de Montjuïc.** … Hasta 120 personas en banquete. El salón hasta las 03:00; la terraza cierra a las 23:30. *[imagen: mirador-montjuic-foto-02]*<br>**Llum del Poblenou.** … Hasta 150 personas en banquete. *[imagen: llum-poblenou-foto-01]*<br>¿Cuál os encaja más? También puedo enseñaros el plano o el recorrido 360°. | La disposición se confirma en la misma frase y se recomienda en el mismo mensaje (§1). Se cuentan dos preguntas: la confirmación y la final |
| C2 | Sí, banquete. El Mirador. | `preferred_location`: "Mirador de Montjuïc" |
| B2 | Perfecto. ¿Tenéis ya un día concreto? ¿Y un presupuesto aproximado? | `datos_consulta.py` → [dia_exacto, presupuesto] |
| C3 | El 20 de noviembre. Unos 4.000 €. | **Día exacto más tarde (§1) → se vuelve a validar.** 20/11 − 8/11 = 12 días.<br>`recomendar.py --validar sp-mirador-montjuic --asistentes 100 --disposicion banquet --dias 12 --hora-fin 00:00` → **encaja** (el Mirador pide 10 días; faltan 12), con `avisos_zona` terraza 23:30 |
| B3 | Para el 20 de noviembre el Mirador llega bien. ¿Necesitaréis algo especial, como catering o audiovisuales? | La revalidación pasa; sigue el cualificador |

**Variante (extra): "el 15 de noviembre".** Con el 20 de noviembre el Mirador encaja, así que he añadido el caso en que no llega.

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C3' | El 15 de noviembre. | 15/11 − 8/11 = 7 días. `--validar … --dias 7` → **no encaja**: antelación ("necesita 10 días; faltan 7"); alternativas: Llum del Poblenou (`comodo`) |
| B3' | Para el 15 de noviembre, el Mirador de Montjuïc no llega: necesita 10 días de preparación. Para esa fecha encaja el Llum del Poblenou, con sitio para 150 personas en banquete. *[imagen: llum-poblenou-foto-01, Imagen ilustrativa]* ¿Os encaja el Llum? | Frase de descarte por antelación (§4) con el dato del script, y la alternativa que da el script. Si elige el Llum, `preferred_location` cambia a "Llum del Poblenou" |

- **¿Cumple?** **Sí.**
  - Al llegar el día exacto se vuelve a validar el espacio elegido.
  - Con 12 días el Mirador encaja. Con 7 no llega: se explica con el dato del script y se propone la alternativa del script.
- **Nota:** el enunciado esperaba que con el 20 de noviembre el Mirador no llegara, pero faltan 12 días y pide 10, así que encaja. Por eso he añadido la variante del 15.

## 4. "Fiesta para 100 hasta la 1" en el Mirador

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C1 | Queremos hacer una fiesta para 100 personas hasta la 1 en el Mirador. | Fiesta → `cocktail`. "La 1" sin más contexto → 01:00 (madrugada).<br>`recomendar.py --validar sp-mirador-montjuic --asistentes 100 --disposicion cocktail --hora-fin 01:00` → **encaja**, `avisos_zona` [terraza hasta las 23:30], grupo `bajo_60` (48 %, dato interno) |
| | | Foto: `foto_tarjeta` con la terraza con aviso → **mirador-montjuic-foto-02** (interior). La foto de cóctel es de la terraza (foto-01) y queda fuera porque la terraza cierra antes (media §2). `--validar` no devuelve la foto: la he sacado con la función del script |
| | | `datos_consulta.py --tipo fiesta --asistentes 100 --espacio "Mirador de Montjuïc"` → preguntas [fecha, presupuesto] |
| B1 | [aviso de IA] Para una fiesta lo normal es formato cóctel; ¿os encaja?<br>**Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Tiene sitio para 210 personas en cóctel. El salón hasta las 03:00; la terraza cierra a las 23:30. *[imagen: mirador-montjuic-foto-02, Imagen ilustrativa]*<br>¿Para qué fecha sería? | "Fiesta" no está en los `event_types` del Mirador, así que la frase se limita al dato (§3). El aviso de la terraza sale de `--validar`. Dos preguntas: la confirmación del formato y la fecha |

- **¿Cumple?** **Sí.**
  - El aviso de la terraza lo da ahora el script, también al validar.
  - La foto no es de la terraza.
  - No se dice "por qué encaja" con un tipo que no está en los datos.
- **Pero:**
  - El Mirador queda `bajo_60` (48 %), y la skill no dice si se avisa al cliente cuando el espacio lo ha elegido él. La frase de `bajo_60` es para cuando no hay otra opción. No lo he dicho (comentario 2).
  - `--validar` no devuelve la foto de la tarjeta (comentario 1).

**Resultado:** los 4 casos cumplen la skill nueva, con la variante extra del caso 3.

## Comentarios

1. **`--validar` no devuelve la foto de la tarjeta.** Con `avisos_zona` resuelto, la tarjeta de un espacio elegido todavía necesita la foto. La regla de media §2 (no usar la foto de una zona con aviso) la aplica `foto_tarjeta`, y `--validar` no la llama. En el caso 4 la he sacado con la función del script.
2. **Espacio elegido `bajo_60`.** Si el cliente elige un espacio mucho más grande de lo que necesita (Mirador para 100 en cóctel), la skill no dice si se avisa o si se proponen otros.
3. **Ejemplo de la §7.** El de la cena dice "hasta 150 en banquete; pensado para cenas de gala", que copia `best_for` ("Cenas de gala"). La §3 dice que la frase nunca copia `best_for` literalmente. En las pruebas he usado "Encaja para una cena de empresa".
4. **La consulta de 500 personas sin zona.** `preferred_location` irá vacío si el cliente no da una zona. En el flujo de Ale, eso también impide el email automático, pero el equipo recibe el aviso igualmente.
