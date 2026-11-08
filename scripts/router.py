#!/usr/bin/env python3
"""Decide qué se hace con las intenciones de un mensaje, con la tabla de la §2
y la prioridad de la §5 de .claude/skills/router-intenciones/SKILL.md
(versión adaptada a la integración con n8n, KNOWLEDGE.md §3.2).

El LLM solo clasifica el mensaje en una o varias intenciones de la lista cerrada.
Este script devuelve, sin interpretar texto:
  - las intenciones ordenadas por prioridad;
  - las skills que entran con cada una (guardrails siempre);
  - la decisión y el motivo cuando la tabla los fija;
  - la acción: contacto_equipo (cambio_reserva, queja, persona sin consulta en
    marcha) u ofrecer_envio (persona con consulta en marcha);
  - a_n8n: si la conversación acabará en un envío a n8n (solo nuevo_evento, o
    persona con consulta en marcha si acepta enviarla);
  - la ruta que se registra (la de la intención más prioritaria) y
    rutas_adicionales (las de las demás intenciones del mensaje).

Uso:
  python3 scripts/router.py nuevo_evento
  python3 scripts/router.py queja nuevo_evento
  python3 scripts/router.py persona --ruta-tema lead
  python3 scripts/router.py persona --consulta-en-marcha
  python3 scripts/router.py queja --legal

Un saludo solo ("Hola") no es una intención: no se llama al script.
"""

import argparse
import json
import sys

SIEMPRE = "guardrails"  # "Guardrails se aplica siempre, además de lo que diga la tabla."

# Tabla de la §2. skills_si_toca: las que la tabla pone "si pide…" o "cuando toque".
# La antigua intención reserva se junta con nuevo_evento (§3.2, decisión 8).
TABLA = {
    "informacion": {"skills": [], "skills_si_toca": ["media-espacios"],
                    "decision": None, "motivo": None, "accion": None, "a_n8n": False, "ruta": "informacion"},
    "nuevo_evento": {"skills": ["recomendador-espacios", "cualificador-leads"],
                     "skills_si_toca": ["media-espacios", "consentimiento"],
                     "decision": None, "motivo": None, "accion": None, "a_n8n": True, "ruta": "lead"},
    "cambio_reserva": {"skills": [], "skills_si_toca": [],
                       "decision": "escalar_humano", "motivo": "cambio_reserva",
                       "accion": "contacto_equipo", "a_n8n": False, "ruta": "cambio"},
    "queja": {"skills": [], "skills_si_toca": [],
              "decision": "escalar_humano", "motivo": "queja",
              "accion": "contacto_equipo", "a_n8n": False, "ruta": "incidencia"},
    "privacidad": {"skills": ["consentimiento"], "skills_si_toca": [],
                   "decision": "escalar_humano", "motivo": "privacidad",
                   "accion": None, "a_n8n": False, "ruta": "privacidad"},
    # persona: accion y a_n8n dependen de si hay una consulta en marcha (ver enrutar)
    "persona": {"skills": [], "skills_si_toca": [],
                "decision": "escalar_humano", "motivo": "peticion_humano",
                "accion": "contacto_equipo", "a_n8n": False, "ruta": None},
    "fuera_tema": {"skills": [], "skills_si_toca": [],
                   "decision": None, "motivo": None, "accion": None, "a_n8n": False, "ruta": "fuera_tema"},
}

# Prioridad de la §5 (menor número = antes).
PRIORIDAD = {"privacidad": 1, "queja": 2, "persona": 3, "cambio_reserva": 4,
             "nuevo_evento": 5, "informacion": 6, "fuera_tema": 7}

# Valores de ruta del registro (KNOWLEDGE.md §3)
RUTAS = ("informacion", "lead", "cambio", "incidencia", "privacidad", "fuera_tema")
RUTA_PERSONA_SIN_TEMA = "incidencia"
RUTA_CONSULTA_EN_MARCHA = "lead"   # la consulta en marcha es un nuevo_evento


def enrutar(intenciones, ruta_tema=None, legal=False, consulta_en_marcha=False):
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
    # (la más prioritaria de las demás); si no hay otra, ruta_tema; si no, la de la
    # consulta en marcha (lead); si no, incidencia.
    otras = [i for i in ordenadas if i != "persona"]
    if otras:
        tema_persona = TABLA[otras[0]]["ruta"]
    else:
        tema_persona = ruta_tema or (RUTA_CONSULTA_EN_MARCHA if consulta_en_marcha else RUTA_PERSONA_SIN_TEMA)

    acciones, skills, skills_si_toca = [], [SIEMPRE], []
    for i in ordenadas:
        fila = TABLA[i]
        motivo = "legal" if (i == "queja" and legal) else fila["motivo"]
        ruta = tema_persona if i == "persona" else fila["ruta"]
        accion, a_n8n = fila["accion"], fila["a_n8n"]
        if i == "persona" and consulta_en_marcha:
            # se ofrece cerrar y enviar la consulta ya, y además el contacto del equipo
            accion, a_n8n = "ofrecer_envio", True
        skills_fila, si_toca_fila = fila["skills"], fila["skills_si_toca"]
        if i == "persona" and consulta_en_marcha:
            si_toca_fila = ["consentimiento"]   # si acepta el envío: pregunta de privacidad
        acciones.append({"intencion": i, "skills": skills_fila, "skills_si_toca": si_toca_fila,
                         "decision": fila["decision"], "motivo_escalado": motivo,
                         "accion": accion, "a_n8n": a_n8n, "ruta": ruta})
        skills += [s for s in skills_fila if s not in skills]
        skills_si_toca += [s for s in si_toca_fila if s not in skills and s not in skills_si_toca]

    # Decisión: la de la intención más prioritaria que la fija
    con_decision = next((a for a in acciones if a["decision"]), None)
    con_accion = next((a for a in acciones if a["accion"]), None)
    return {
        "intenciones": ordenadas,
        "skills": skills,
        "skills_si_toca": [s for s in skills_si_toca if s not in skills],
        "decision": con_decision["decision"] if con_decision else None,
        "motivo_escalado": con_decision["motivo_escalado"] if con_decision else None,
        "accion": con_accion["accion"] if con_accion else None,
        "a_n8n": any(a["a_n8n"] for a in acciones),
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
    p.add_argument("--consulta-en-marcha", action="store_true",
                   help="para persona: hay una consulta de evento en marcha (se ofrece enviarla ya)")
    a = p.parse_args()
    try:
        r = enrutar(a.intenciones, a.ruta_tema, a.legal, a.consulta_en_marcha)
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
