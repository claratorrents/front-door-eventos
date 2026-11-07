#!/usr/bin/env python3
"""Casos de prueba del cualificador, calculados por el equipo.

Cada caso traduce la frase del cliente a niveles con la tabla de la §3 de la
skill (eso lo hace el chatbot; aquí se fija para que el test sea estable).
Las fechas de "hoy" son fijas para que "este mes" no dependa del día en que
se ejecuta el test.

Uso:  python3 scripts/test_puntuar_lead.py
Sale con código 0 si todos pasan y 1 si alguno falla.
"""

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from puntuar_lead import puntuar  # noqa: E402

HOY = datetime.date(2026, 11, 7)

# (descripción, argumentos, puntuación esperada, decisión esperada, comprobaciones del desglose)
CASOS = [
    ("Cena 120 en marzo, 'unos 6.000 €', empresa con nombre, decide esta semana",
     dict(fecha="mes_o_rango", asistentes="concreto", presupuesto="aproximado",
          tipo_evento="cena", primer_recomendado="sp-llum-poblenou",
          empresa="corporativo_con_nombre", urgencia="14_dias_o_menos"),
     80, "escalar_comercial", {}),
    ("Igual, con día exacto, Llum elegido y antelación OK",
     dict(fecha="dia_exacto", asistentes="concreto", presupuesto="aproximado",
          tipo_evento="cena", primer_recomendado="sp-llum-poblenou",
          espacio_elegido="sp-llum-poblenou", antelacion_cumplida=True,
          empresa="corporativo_con_nombre", urgencia="14_dias_o_menos"),
     90, "prerreserva", {}),
    ("Boda para unos 100 el año que viene, sin presupuesto, particular, sin prisa",
     dict(fecha="temporada_o_anio", asistentes="aproximado", presupuesto="no_sabe",
          tipo_evento="boda", primer_recomendado="sp-mirador-montjuic",
          empresa="particular", urgencia="sin_prisa"),
     30, "escalar_comercial", {"tipo": 10}),
    ("Formación para 20 el 3 de diciembre, 800-1.000 €, empresa, 'este mes' (7/11), elige Atelier",
     dict(fecha="dia_exacto", asistentes="concreto", presupuesto="aproximado",
          tipo_evento="formacion", primer_recomendado="sp-atelier-sant-antoni",
          espacio_elegido="sp-atelier-sant-antoni", antelacion_cumplida=True,
          empresa="corporativo_con_nombre", urgencia="este_mes", hoy=HOY),
     85, "prerreserva", {"urgencia": 5}),
    ("Conferencia para unos 100 el 20 de enero, 2.000-3.000 €, empresa, sin prisa",
     dict(fecha="dia_exacto", asistentes="aproximado", presupuesto="aproximado",
          tipo_evento="conferencia", primer_recomendado="sp-forum-les-corts",
          empresa="corporativo_con_nombre", urgencia="sin_prisa"),
     70, "escalar_comercial", {}),
    # Casos nuevos (solo se comprueba el criterio indicado)
    ("Boda sin espacio recomendado y tipo claro → tipo 10",
     dict(tipo_evento="boda"), None, None, {"tipo": 10}),
    ("'Somos una empresa' sin nombre → empresa 5",
     dict(empresa="corporativo_sin_nombre"), None, None, {"empresa": 5}),
    ("'Este mes' un día 20 (quedan 10 días) → urgencia 10",
     dict(urgencia="este_mes", hoy=datetime.date(2026, 11, 20)), None, None, {"urgencia": 10}),
    ("'Este mes' un día 5 (quedan 25 días) → urgencia 5",
     dict(urgencia="este_mes", hoy=datetime.date(2026, 11, 5)), None, None, {"urgencia": 5}),
    ("Espacio elegido manda sobre el primero recomendado (conferencia: Fòrum sí, Mirador no) → tipo 10",
     dict(tipo_evento="conferencia", primer_recomendado="sp-forum-les-corts",
          espacio_elegido="sp-mirador-montjuic"), None, None, {"tipo": 10}),
]


def main():
    fallos = 0
    for nombre, args, puntos, decision, criterios in CASOS:
        r = puntuar(**args)
        ok = True
        if puntos is not None and r["puntuacion"] != puntos:
            ok = False
        if decision is not None and r["decision"] != decision:
            ok = False
        for criterio, esperado in criterios.items():
            if r["desglose"][criterio]["puntos"] != esperado:
                ok = False
        resumen = f"{r['puntuacion']}, {r['decision']}" if puntos is not None else \
            ", ".join(f"{c} {r['desglose'][c]['puntos']}" for c in criterios)
        print(f"{'OK   ' if ok else 'FALLO'} {nombre} → {resumen}")
        if not ok:
            fallos += 1
            print(f"      esperado: {puntos}, {decision}, {criterios}")
            print(f"      desglose: { {c: d['puntos'] for c, d in r['desglose'].items()} }")
    print(f"\n{len(CASOS) - fallos}/{len(CASOS)} casos correctos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
