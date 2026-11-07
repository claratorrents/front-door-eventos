# Corrección 06 · Media de espacios

Fecha: 7 de noviembre de 2026
Archivos: `.claude/skills/media-espacios/SKILL.md`, `data/espacios.json` (`disposition`, `illustrative`, `zone`), `scripts/recomendar.py`, `scripts/test_recomendar.py`, `scripts/validar_datos.py`
Pruebas: `pruebas/prueba-media-01.md` (antes) y `pruebas/prueba-media-02.md` (después)

## Antes

Primera versión de la skill, escrita por el equipo. Se añadió `disposition` a las 12 fotos y el script pasó a elegir la foto de cada tarjeta. Los 14 tests pasaron y en 1.600 combinaciones nunca salió una foto no aprobada. Las 5 frases de la prueba 01 cumplieron, pero quedaban tres huecos.

## Problema

| # | Qué falló o no convencía en la prueba 01 |
|---|---|
| 1 | "Imagen ilustrativa" (§5) no se podía aplicar: ningún dato decía qué imágenes son ilustrativas, y deducirlo de la ruta sería suponer. |
| 2 | Foto de la terraza del Mirador en eventos en los que la terraza ya está cerrada (fiesta hasta las 3) y en una conferencia, porque no hay foto de teatro y salía la primera aprobada, que es la terraza. |
| 3 | Las fotos adicionales, el plano y el tour los buscaba el LLM en los datos, sin la garantía del script. |

## Cambio (decidido por el equipo)

| # | Decisión | Dónde |
|---|---|---|
| 1 | `illustrative: true` en los 24 elementos de media; el validador lo exige (true/false). Skill: "Si el elemento tiene illustrative: true, el pie lo indica". El script devuelve `illustrative` con cada elemento. | Datos, validador, skill §5, script |
| 2 | `zone: "terraza"` en la foto 1 del Mirador. Al elegir la foto de la tarjeta: nunca una de una zona con aviso de cierre; si no hay foto con la misma disposición, mejor una de interior (sin `zone`). Skill: "Nunca una foto de una zona que cierra antes del fin del evento. Si no hay foto con la misma disposición, mejor una de interior que una de una zona exterior." | Datos, validador, script, skill §2 |
| 3 | Nueva función `media_aprobada(espacio, tipo)` (también `--media ID --tipo foto|plano|tour360|video`): devuelve la media aprobada sin `url`. Skill: "Las fotos adicionales, el plano y el tour se piden al script; el LLM no los busca en los datos." | Script, skill §3 |

## Después

- `scripts/test_recomendar.py`: **20/20**.
  - Los 14 de antes siguen pasando.
  - Dos casos nuevos de foto: fiesta de 100 hasta las 03:00 → Mirador foto-02; conferencia de 150 → Mirador foto-02.
  - Cuatro casos de media: fotos del Jardí (solo la 01), plano del Mirador, tour de la Nau y vídeo de la Nau (ninguno), siempre sin `url`.
- Validador: todo correcto con los datos reales. En una copia detecta que falta `illustrative`, que `illustrative` no es true/false y que `zone` está vacío.
- Prueba 02 (las 5 frases de la 01 y la conferencia de 150): las 6 cumplen, con "Imagen ilustrativa" en todos los pies y el Mirador sin la foto de la terraza en la conferencia.
- Quedan abiertos, sin hacer fallar la prueba:
  - En la conferencia, la foto del Mirador es de banquete (falta una foto de teatro).
  - El criterio "interior = sin `zone`" depende de marcar todas las fotos de exterior; la del patio del Jardí no lo está.
