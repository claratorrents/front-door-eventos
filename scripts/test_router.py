#!/usr/bin/env python3
"""Casos de prueba del router, calculados por el equipo.

Uso:  python3 scripts/test_router.py
Sale con código 0 si todos pasan y 1 si alguno falla.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from router import enrutar  # noqa: E402

# (descripción, intenciones, opciones, comprobaciones)
CASOS = [
    ("nuevo_evento → ruta lead, recomendador + cualificador", ["nuevo_evento"], {},
     {"ruta": "lead", "skills_incluye": ["recomendador-espacios", "cualificador-leads"]}),
    ("reserva → ruta reserva", ["reserva"], {}, {"ruta": "reserva"}),
    ("cambio_reserva → escalar_humano, cambio_reserva, ruta cambio", ["cambio_reserva"], {},
     {"decision": "escalar_humano", "motivo_escalado": "cambio_reserva", "ruta": "cambio"}),
    ("queja + nuevo_evento → [queja, nuevo_evento], ruta incidencia", ["queja", "nuevo_evento"], {},
     {"intenciones": ["queja", "nuevo_evento"], "ruta": "incidencia"}),
    ("informacion + privacidad → [privacidad, informacion], ruta privacidad", ["informacion", "privacidad"], {},
     {"intenciones": ["privacidad", "informacion"], "ruta": "privacidad"}),
    ("persona sin tema → ruta incidencia", ["persona"], {}, {"ruta": "incidencia"}),
    ("persona con tema lead → ruta lead", ["persona"], {"ruta_tema": "lead"}, {"ruta": "lead"}),
    ("fuera_tema → ruta fuera_tema", ["fuera_tema"], {}, {"ruta": "fuera_tema"}),
    # Ronda 2
    ("queja + nuevo_evento → ruta incidencia, rutas_adicionales [lead]", ["queja", "nuevo_evento"], {},
     {"ruta": "incidencia", "rutas_adicionales": ["lead"]}),
    ("persona + nuevo_evento → ruta lead", ["persona", "nuevo_evento"], {}, {"ruta": "lead"}),
    ("reserva → incluye recomendador", ["reserva"], {}, {"skills_incluye": ["recomendador-espacios"]}),
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

    # Intención fuera de la lista → error
    try:
        enrutar(["comprar_entradas"])
        ok = False
    except ValueError:
        ok = True
    print(f"{'OK   ' if ok else 'FALLO'} intención fuera de la lista → error")
    fallos += 0 if ok else 1

    total = len(CASOS) + 1
    print(f"\n{total - fallos}/{total} casos correctos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
