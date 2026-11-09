#!/usr/bin/env python3
"""Decide qué datos faltan en una consulta de evento y qué preguntar después,
con las reglas de las §2 y §4 de .claude/skills/cualificador-leads/SKILL.md.

No puntúa: la puntuación oficial la hace n8n (KNOWLEDGE.md §3.2).

Datos, en el orden de la §2:
  1. tipo            tipo de evento                         (imprescindible)
  2. asistentes      número o rango                         (imprescindible)
  3. espacio_o_zona  espacio elegido o, si no, zona         (imprescindible)
  4. fecha           día, mes o temporada                   (imprescindible)
  5. dia_exacto      solo si la fecha es mes o temporada    (recomendable)
  6. presupuesto     número o rango                         (recomendable)
  7. necesidades     catering, audiovisuales, extras…       (recomendable)

Reglas (§4):
  - Un dato queda cerrado si está dado, si el cliente contestó a esa pregunta
    (aunque sea "no lo sé" o "aún no": --respondidos) o si ya se le preguntó dos
    veces sin respuesta (el dato aparece dos veces en --preguntados).
  - Si el cliente cambia de tema sin contestar, la pregunta sigue pendiente: vuelve a
    salir después de atender su tema.
  - Faltan los datos que no están cerrados, en el orden de la §2.
  - Siguientes preguntas: las dos primeras que faltan.
  - listo_para_enviar: verdadero cuando no falta ninguno.

Uso:
  python3 scripts/datos_consulta.py --tipo "cena de empresa" --asistentes 120 \\
      --espacio "Llum del Poblenou" --fecha mes --preguntados dia_exacto,presupuesto \\
      --respondidos presupuesto
  --fecha: dia / mes / temporada / nada (por defecto, nada)
  --preguntados: cada vez que el chatbot hace una pregunta, su dato (se repite si se
                 pregunta dos veces), separados por comas
  --respondidos: datos cuya pregunta el cliente contestó, aunque fuera "no lo sé"

Salida (JSON): datos_que_faltan, siguientes_preguntas y listo_para_enviar.
"""

import argparse
import json

ORDEN = ["tipo", "asistentes", "espacio_o_zona", "fecha", "dia_exacto", "presupuesto", "necesidades"]
NIVELES_FECHA = ["dia", "mes", "temporada", "nada"]
MAX_PREGUNTAS = 2
MAX_VECES_SIN_RESPUESTA = 2   # tras dos preguntas sin respuesta, el dato queda cerrado


def _dado(valor):
    return valor is not None and str(valor).strip() != ""


def datos_consulta(tipo=None, asistentes=None, espacio=None, zona=None, fecha="nada",
                   presupuesto=None, necesidades=None, preguntados=(), respondidos=()):
    if fecha not in NIVELES_FECHA:
        raise ValueError(f"fecha '{fecha}' no es una de {NIVELES_FECHA}")
    desconocidos = (set(preguntados) | set(respondidos)) - set(ORDEN)
    if desconocidos:
        raise ValueError(f"datos desconocidos: {sorted(desconocidos)}; deben ser de {ORDEN}")

    dados = {
        "tipo": _dado(tipo),
        "asistentes": _dado(asistentes),
        "espacio_o_zona": _dado(espacio) or _dado(zona),   # sin espacio, basta la zona
        "fecha": fecha != "nada",                           # día, mes o temporada
        "presupuesto": _dado(presupuesto),
        "necesidades": _dado(necesidades),
    }
    # Dato 5: el día exacto solo se pide si la fecha es mes o temporada
    aplica = {d: True for d in ORDEN}
    aplica["dia_exacto"] = fecha in ("mes", "temporada")
    dados["dia_exacto"] = fecha == "dia"

    preguntados = list(preguntados)
    cerrado = {d: dados[d] or d in respondidos or preguntados.count(d) >= MAX_VECES_SIN_RESPUESTA
               for d in ORDEN}
    faltan = [d for d in ORDEN if aplica[d] and not cerrado[d]]
    return {
        "datos_que_faltan": faltan,
        "siguientes_preguntas": faltan[:MAX_PREGUNTAS],
        "listo_para_enviar": not faltan,
    }


def main():
    ap = argparse.ArgumentParser(description="Datos que faltan en una consulta de evento (reglas fijas)")
    ap.add_argument("--tipo")
    ap.add_argument("--asistentes")
    ap.add_argument("--espacio")
    ap.add_argument("--zona")
    ap.add_argument("--fecha", choices=NIVELES_FECHA, default="nada")
    ap.add_argument("--presupuesto")
    ap.add_argument("--necesidades")
    ap.add_argument("--preguntados", default="", help="un dato por cada vez que se preguntó, separados por comas")
    ap.add_argument("--respondidos", default="", help="datos cuya pregunta contestó el cliente, separados por comas")
    a = ap.parse_args()
    preguntados = [p.strip() for p in a.preguntados.split(",") if p.strip()]
    respondidos = [p.strip() for p in a.respondidos.split(",") if p.strip()]
    r = datos_consulta(a.tipo, a.asistentes, a.espacio, a.zona, a.fecha,
                       a.presupuesto, a.necesidades, preguntados, respondidos)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
