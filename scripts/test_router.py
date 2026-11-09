#!/usr/bin/env python3
"""Casos de prueba del router, calculados por el equipo.

Uso:  python3 scripts/test_router.py
Sale con código 0 si todos pasan y 1 si alguno falla.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from router import enrutar  # noqa: E402

# (descripción, intenciones, opciones, comprobaciones). Esperados del equipo
# (versión adaptada a n8n, KNOWLEDGE.md §3.2).
CASOS = [
    ("nuevo_evento → ruta lead, guardrails + recomendador + cualificador, si toca media + consentimiento + envio-n8n, a_n8n true",
     ["nuevo_evento"], {},
     {"ruta": "lead", "skills": ["guardrails", "recomendador-espacios", "cualificador-leads"],
      "skills_si_toca": ["media-espacios", "consentimiento", "envio-n8n"], "a_n8n": True}),
    ("cambio_reserva → escalar_humano, cambio_reserva, ruta cambio, solo guardrails, a_n8n false",
     ["cambio_reserva"], {},
     {"decision": "escalar_humano", "motivo_escalado": "cambio_reserva", "ruta": "cambio",
      "skills": ["guardrails"], "skills_si_toca": [], "a_n8n": False}),
    ("queja + nuevo_evento → [queja, nuevo_evento], ruta incidencia, rutas_adicionales [lead], a_n8n true",
     ["queja", "nuevo_evento"], {},
     {"intenciones": ["queja", "nuevo_evento"], "ruta": "incidencia", "rutas_adicionales": ["lead"], "a_n8n": True}),
    ("persona sin tema → ruta incidencia, accion contacto_equipo, a_n8n false", ["persona"], {},
     {"ruta": "incidencia", "accion": "contacto_equipo", "a_n8n": False}),
    ("persona + nuevo_evento → ruta lead", ["persona", "nuevo_evento"], {}, {"ruta": "lead"}),
    ("persona --consulta-en-marcha → accion ofrecer_envio, a_n8n true", ["persona"], {"consulta_en_marcha": True},
     {"accion": "ofrecer_envio", "a_n8n": True}),
    ("persona --consulta-en-marcha → consentimiento y envio-n8n en skills_si_toca", ["persona"], {"consulta_en_marcha": True},
     {"skills": ["guardrails"], "skills_si_toca": ["consentimiento", "envio-n8n"]}),
    ("privacidad + informacion → [privacidad, informacion], ruta privacidad, incluye consentimiento",
     ["privacidad", "informacion"], {},
     {"intenciones": ["privacidad", "informacion"], "ruta": "privacidad", "skills_incluye": ["consentimiento"]}),
    ("privacidad → escalar_humano, motivo privacidad", ["privacidad"], {},
     {"decision": "escalar_humano", "motivo_escalado": "privacidad", "ruta": "privacidad"}),
    ("fuera_tema → ruta fuera_tema, a_n8n false", ["fuera_tema"], {}, {"ruta": "fuera_tema", "a_n8n": False}),
]
ERRORES = [
    ("reserva → error (ya no es una intención)", ["reserva"]),
    ("intención fuera de la lista → error", ["comprar_entradas"]),
]


def main():
    fallos = 0
    for nombre, intenciones, opciones, esperado in CASOS:
        r = enrutar(intenciones, **opciones)
        ok = True
        for campo, valor in esperado.items():
            if campo == "skills_incluye":
                ok &= all(s in r["skills"] for s in valor)
            else:
                ok &= r[campo] == valor
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      esperado: {esperado}\n      obtenido: {r}")

    # Intenciones fuera de la lista → error
    for nombre, intenciones in ERRORES:
        try:
            enrutar(intenciones)
            ok = False
        except ValueError:
            ok = True
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        fallos += 0 if ok else 1

    total = len(CASOS) + len(ERRORES)
    print(f"\n{total - fallos}/{total} casos correctos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
