#!/usr/bin/env python3
"""Decide qué se hace con las intenciones de un mensaje, con la tabla de la §2
y la prioridad de la §4 de .claude/skills/router-intenciones/SKILL.md.

El LLM solo clasifica el mensaje en una o varias intenciones de la lista cerrada.
Este script devuelve, sin interpretar texto:
  - las intenciones ordenadas por prioridad;
  - las skills que entran con cada una (guardrails siempre);
  - la decisión y el motivo cuando la tabla los fija;
  - la ruta que se registra (la de la intención más prioritaria) y
    rutas_adicionales (las de las demás intenciones del mensaje).

Uso:
  python3 scripts/router.py nuevo_evento
  python3 scripts/router.py queja nuevo_evento
  python3 scripts/router.py persona --ruta-tema lead
  python3 scripts/router.py queja --legal

Un saludo solo ("Hola") no es una intención: no se llama al script.
"""

import argparse
import json
import sys

SIEMPRE = "guardrails"  # "Guardrails se aplica siempre, además de lo que diga la tabla."

# Tabla de la §2. skills_si_toca: las que la tabla pone "si pide…" o "cuando toque".
TABLA = {
    "informacion": {"skills": [], "skills_si_toca": ["media-espacios"],
                    "decision": None, "motivo": None, "ruta": "informacion"},
    "nuevo_evento": {"skills": ["recomendador-espacios", "cualificador-leads"],
                     "skills_si_toca": ["media-espacios", "consentimiento"],
                     "decision": None, "motivo": None, "ruta": "lead"},
    "reserva": {"skills": ["cualificador-leads", "recomendador-espacios", "consentimiento"], "skills_si_toca": [],
                "decision": None, "motivo": None, "ruta": "reserva"},
    "cambio_reserva": {"skills": ["consentimiento"], "skills_si_toca": [],
                       "decision": "escalar_humano", "motivo": "cambio_reserva", "ruta": "cambio"},
    "queja": {"skills": ["consentimiento"], "skills_si_toca": [],
              "decision": "escalar_humano", "motivo": "queja", "ruta": "incidencia"},
    "privacidad": {"skills": ["consentimiento"], "skills_si_toca": [],
                   "decision": None, "motivo": None, "ruta": "privacidad"},
    "persona": {"skills": ["consentimiento"], "skills_si_toca": [],
                "decision": "escalar_humano", "motivo": "peticion_humano", "ruta": None},
    "fuera_tema": {"skills": [], "skills_si_toca": [],
                   "decision": None, "motivo": None, "ruta": "fuera_tema"},
}

# Prioridad de la §4 (menor número = antes). reserva y nuevo_evento comparten nivel.
PRIORIDAD = {"privacidad": 1, "queja": 2, "persona": 3, "cambio_reserva": 4,
             "reserva": 5, "nuevo_evento": 5, "informacion": 6, "fuera_tema": 7}

# Valores de ruta del contrato (KNOWLEDGE.md §3)
RUTAS = ("informacion", "lead", "reserva", "cambio", "incidencia", "privacidad", "fuera_tema")
RUTA_PERSONA_SIN_TEMA = "incidencia"


def enrutar(intenciones, ruta_tema=None, legal=False):
    if not intenciones:
        raise ValueError("hace falta al menos una intención (un saludo solo no es una intención)")
    desconocidas = [i for i in intenciones if i not in TABLA]
    if desconocidas:
        raise ValueError(f"intención fuera de la lista: {desconocidas}; válidas: {list(TABLA)}")
    if ruta_tema is not None and ruta_tema not in RUTAS:
        raise ValueError(f"ruta_tema {ruta_tema!r} no es una de {RUTAS}")

    # Sin repetidas; orden estable por prioridad (a igual prioridad, el orden de entrada)
    unicas = list(dict.fromkeys(intenciones))
    ordenadas = sorted(unicas, key=lambda i: PRIORIDAD[i])

    # persona con otra intención: la ruta del tema es la de esa otra intención
    # (la más prioritaria de las demás); si no hay otra, ruta_tema; si no, incidencia.
    otras = [i for i in ordenadas if i != "persona"]
    tema_persona = TABLA[otras[0]]["ruta"] if otras else (ruta_tema or RUTA_PERSONA_SIN_TEMA)

    acciones, skills, skills_si_toca = [], [SIEMPRE], []
    for i in ordenadas:
        fila = TABLA[i]
        motivo = "legal" if (i == "queja" and legal) else fila["motivo"]
        ruta = tema_persona if i == "persona" else fila["ruta"]
        acciones.append({"intencion": i, "skills": fila["skills"], "skills_si_toca": fila["skills_si_toca"],
                         "decision": fila["decision"], "motivo_escalado": motivo, "ruta": ruta})
        skills += [s for s in fila["skills"] if s not in skills]
        skills_si_toca += [s for s in fila["skills_si_toca"] if s not in skills and s not in skills_si_toca]

    # Decisión: la de la intención más prioritaria que la fija
    con_decision = next((a for a in acciones if a["decision"]), None)
    return {
        "intenciones": ordenadas,
        "skills": skills,
        "skills_si_toca": [s for s in skills_si_toca if s not in skills],
        "decision": con_decision["decision"] if con_decision else None,
        "motivo_escalado": con_decision["motivo_escalado"] if con_decision else None,
        "ruta": acciones[0]["ruta"],
        "rutas_adicionales": list(dict.fromkeys(
            a["ruta"] for a in acciones[1:] if a["ruta"] != acciones[0]["ruta"])),
        "acciones": acciones,
    }


def main():
    p = argparse.ArgumentParser(description="Router de intenciones por tabla fija")
    p.add_argument("intenciones", nargs="+", help=f"una o varias de: {', '.join(TABLA)}")
    p.add_argument("--ruta-tema", choices=RUTAS, help="para persona: ruta del tema de la conversación")
    p.add_argument("--legal", action="store_true", help="para queja: es un tema legal (motivo legal)")
    a = p.parse_args()
    try:
        r = enrutar(a.intenciones, a.ruta_tema, a.legal)
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
