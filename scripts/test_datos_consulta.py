#!/usr/bin/env python3
"""Casos de prueba de datos_consulta.py, con los esperados del equipo.

Uso:  python3 scripts/test_datos_consulta.py
Sale con código 0 si todos pasan y 1 si alguno falla.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from datos_consulta import datos_consulta  # noqa: E402

BASE = {"tipo": "cena de empresa", "asistentes": "120"}
CON_ESPACIO = {**BASE, "espacio": "Llum del Poblenou"}

# (descripción, entrada, comprobaciones)
CASOS = [
    ("Nada → [tipo, asistentes], listo false", {},
     {"siguientes_preguntas": ["tipo", "asistentes"], "listo_para_enviar": False}),
    ("Tipo y asistentes → [espacio o zona, fecha]", BASE,
     {"siguientes_preguntas": ["espacio_o_zona", "fecha"]}),
    ("Tipo, asistentes, espacio, fecha mes → [día exacto, presupuesto]", {**CON_ESPACIO, "fecha": "mes"},
     {"siguientes_preguntas": ["dia_exacto", "presupuesto"]}),
    ("Igual con fecha temporada → [día exacto, presupuesto]", {**CON_ESPACIO, "fecha": "temporada"},
     {"siguientes_preguntas": ["dia_exacto", "presupuesto"]}),
    ("Todo dado con día exacto → [], listo true",
     {**CON_ESPACIO, "fecha": "dia", "presupuesto": "6.000 €", "necesidades": "audiovisuales"},
     {"siguientes_preguntas": [], "listo_para_enviar": True}),
    ("Fecha mes, ya preguntados día exacto y presupuesto → [necesidades], listo false",
     {**CON_ESPACIO, "fecha": "mes", "preguntados": ["dia_exacto", "presupuesto"]},
     {"siguientes_preguntas": ["necesidades"], "listo_para_enviar": False}),
    ("Lo anterior + ya preguntadas necesidades → [], listo true",
     {**CON_ESPACIO, "fecha": "mes", "preguntados": ["dia_exacto", "presupuesto", "necesidades"]},
     {"siguientes_preguntas": [], "listo_para_enviar": True}),
    ("Sin espacio pero con zona Gràcia → la zona cuenta como dada", {**BASE, "zona": "Gràcia"},
     {"no_falta": "espacio_o_zona"}),
]


def main():
    fallos = 0
    for nombre, entrada, esperado in CASOS:
        r = datos_consulta(**entrada)
        ok = True
        for campo, valor in esperado.items():
            if campo == "no_falta":
                ok &= valor not in r["datos_que_faltan"]
            else:
                ok &= r[campo] == valor
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      esperado: {esperado}\n      obtenido: {r}")

    # Errores de entrada
    for nombre, entrada in [("fecha fuera de la lista → error", {"fecha": "pronto"}),
                            ("dato preguntado desconocido → error", {"preguntados": ["urgencia"]})]:
        try:
            datos_consulta(**entrada)
            ok = False
        except ValueError:
            ok = True
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        fallos += 0 if ok else 1

    total = len(CASOS) + 2
    print(f"\n{total - fallos}/{total} casos correctos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
