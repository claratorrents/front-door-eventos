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
  - Cada dato se pregunta una sola vez: si ya se preguntó (aunque el cliente no
    lo supiera o no contestara), no vuelve a salir.
  - Faltan los datos que no están dados ni preguntados, en el orden de la §2.
  - Siguientes preguntas: las dos primeras que faltan.
  - listo_para_enviar: verdadero cuando cada dato está dado o ya se preguntó.

Uso:
  python3 scripts/datos_consulta.py --tipo "cena de empresa" --asistentes 120 \\
      --espacio "Llum del Poblenou" --fecha mes --preguntados dia_exacto,presupuesto
  --fecha: dia / mes / temporada / nada (por defecto, nada)
  --preguntados: datos ya preguntados, separados por comas (nombres de arriba)

Salida (JSON): datos_que_faltan, siguientes_preguntas y listo_para_enviar.
"""

import argparse
import json

ORDEN = ["tipo", "asistentes", "espacio_o_zona", "fecha", "dia_exacto", "presupuesto", "necesidades"]
NIVELES_FECHA = ["dia", "mes", "temporada", "nada"]
MAX_PREGUNTAS = 2


def _dado(valor):
    return valor is not None and str(valor).strip() != ""


def datos_consulta(tipo=None, asistentes=None, espacio=None, zona=None, fecha="nada",
                   presupuesto=None, necesidades=None, preguntados=()):
    if fecha not in NIVELES_FECHA:
        raise ValueError(f"fecha '{fecha}' no es una de {NIVELES_FECHA}")
    desconocidos = set(preguntados) - set(ORDEN)
    if desconocidos:
        raise ValueError(f"datos preguntados desconocidos: {sorted(desconocidos)}; deben ser de {ORDEN}")

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

    faltan = [d for d in ORDEN if aplica[d] and not dados[d] and d not in preguntados]
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
    ap.add_argument("--preguntados", default="", help="datos ya preguntados, separados por comas")
    a = ap.parse_args()
    preguntados = [p.strip() for p in a.preguntados.split(",") if p.strip()]
    r = datos_consulta(a.tipo, a.asistentes, a.espacio, a.zona, a.fecha,
                       a.presupuesto, a.necesidades, preguntados)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
