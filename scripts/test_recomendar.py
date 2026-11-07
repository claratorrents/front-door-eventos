#!/usr/bin/env python3
"""Casos de prueba del recomendador, calculados por el equipo.

Uso:  python3 scripts/test_recomendar.py
Sale con código 0 si todos pasan y 1 si alguno falla.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recomendar import recomendar  # noqa: E402

# (descripción, argumentos, recomendados esperados [(id, %, grupo)], descartados esperados [(id, motivo)])
CASOS = [
    ("120 banquet", dict(asistentes=120, disposicion="banquet"),
     [("sp-llum-poblenou", 80, "comodo"), ("sp-mirador-montjuic", 100, "al_limite")], []),
    ("140 banquet", dict(asistentes=140, disposicion="banquet"),
     [("sp-nau-besos", 64, "comodo"), ("sp-llum-poblenou", 93, "al_limite")], []),
    ("75 banquet", dict(asistentes=75, disposicion="banquet"),
     [("sp-forum-les-corts", 83, "comodo"), ("sp-mirador-montjuic", 62, "comodo")], []),
    ("33 banquet", dict(asistentes=33, disposicion="banquet"),
     [("sp-atelier-sant-antoni", 94, "al_limite"), ("sp-jardi-gracia", 55, "bajo_60")], []),
    ("150 theater", dict(asistentes=150, disposicion="theater"),
     [("sp-llum-poblenou", 75, "comodo"), ("sp-mirador-montjuic", 94, "al_limite")], []),
    ("100 cocktail, fin 03:00", dict(asistentes=100, disposicion="cocktail", hora_fin="03:00"),
     [("sp-mirador-montjuic", 48, "bajo_60"), ("sp-nau-besos", 25, "bajo_60")],
     [("sp-llum-poblenou", "horario"), ("sp-jardi-gracia", "horario"), ("sp-forum-les-corts", "horario")]),
    ("180 theater, 5 días", dict(asistentes=180, disposicion="theater", dias=5),
     [], [("sp-llum-poblenou", "antelacion"), ("sp-nau-besos", "antelacion")]),
    ("500 cocktail", dict(asistentes=500, disposicion="cocktail"), [], []),
    ("100 cocktail, fin 21:00 (al_limite único + alternativa)",
     dict(asistentes=100, disposicion="cocktail", hora_fin="21:00"),
     [("sp-jardi-gracia", 91, "al_limite"), ("sp-forum-les-corts", 59, "bajo_60")], []),
]


def espacio_prueba(id_, aforo_banquet):
    """Espacio de prueba mínimo (no es del catálogo) para forzar un empate."""
    return {"id": id_, "name": id_,
            "capacities": {"cocktail": aforo_banquet, "theater": aforo_banquet,
                           "banquet": aforo_banquet, "classroom": aforo_banquet},
            "chatbot_guardrails": {"min_lead_time_days": 0, "max_end_time": "05:00"}}


def test_desempate():
    """63 en banquete: A (aforo 90) = 70 % y B (aforo 70) = 90 %. Los dos son comodo y
    están a 10 puntos del 80 %. Gana B, que tiene menos aforo, en cualquier orden del JSON."""
    a, b = espacio_prueba("prueba-a-90", 90), espacio_prueba("prueba-b-70", 70)
    esperado = [("prueba-b-70", 90, "comodo"), ("prueba-a-90", 70, "comodo")]
    ok = True
    for orden in ([a, b], [b, a]):
        r = recomendar(63, "banquet", espacios=orden)
        obtenido = [(x["id"], x["ocupacion"], x["grupo"]) for x in r["recomendados"]]
        if obtenido != esperado:
            ok = False
            print(f"      esperado: {esperado}\n      obtenido: {obtenido}")
    print(f"{'OK   ' if ok else 'FALLO'} desempate (datos de prueba, los dos órdenes)")
    return ok


def test_aviso_zona():
    """Cena de 120 hasta las 00:00: el Mirador avisa de la terraza (23:30); Llum no avisa."""
    r = recomendar(120, "banquet", hora_fin="00:00")
    avisos = {x["id"]: x["avisos_zona"] for x in r["recomendados"]}
    esperado = {"sp-llum-poblenou": [], "sp-mirador-montjuic": [{"zona": "terraza", "hasta": "23:30"}]}
    sin_hora = recomendar(120, "banquet")
    ok = avisos == esperado and all(x["avisos_zona"] == [] for x in sin_hora["recomendados"])
    print(f"{'OK   ' if ok else 'FALLO'} aviso de zona (cena 120 hasta las 00:00)")
    if not ok:
        print(f"      esperado: {esperado}\n      obtenido: {avisos}")
    return ok


def main():
    fallos = 0
    for nombre, args, esp_rec, esp_desc in CASOS:
        r = recomendar(**args)
        rec = [(x["id"], x["ocupacion"], x["grupo"]) for x in r["recomendados"]]
        desc = sorted((x["id"], x["motivo"]) for x in r["descartados"])
        ok = rec == esp_rec and desc == sorted(esp_desc)
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      esperado: {esp_rec} · descartados {sorted(esp_desc)}")
            print(f"      obtenido: {rec} · descartados {desc}")
    if not test_desempate():
        fallos += 1
    if not test_aviso_zona():
        fallos += 1
    total = len(CASOS) + 2
    print(f"\n{total - fallos}/{total} casos correctos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
