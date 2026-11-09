#!/usr/bin/env python3
"""Casos de prueba de enviar_n8n.py (borradores/punto7-script.md, tests 1-12).

Solo datos sintéticos y sin red externa: el caso 11 usa un servidor local de prueba
(http.server en 127.0.0.1, puerto libre) y una clave aleatoria generada en el momento.
Las pruebas escriben en un registro temporal, nunca en registros/conversaciones.jsonl.

Uso:  python3 scripts/test_enviar_n8n.py
Sale con código 0 si todos pasan y 1 si alguno falla.
"""

import copy
import datetime
import json
import re
import secrets
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from enviar_n8n import CAMPOS, FRASES, procesar  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="test_enviar_n8n_"))
_n = 0


def registro_nuevo():
    global _n
    _n += 1
    return TMP / f"registro-{_n}.jsonl"


BASE = {
    "id_conversacion": "conv-test-01", "idioma": "es",
    "ruta": "lead", "rutas_adicionales": [], "decision": "ninguna", "motivo_escalado": None,
    "consulta": {"tipo_evento": "cena de empresa", "asistentes": "80", "espacio_elegido": "Mirador de Montjuïc",
                 "zona": "", "fecha": "2026-12-12", "presupuesto": "6.000 €",
                 "necesidades": "Necesitan pantalla y sonido", "escalados": ["Pide descuento"]},
    "cliente": {"nombre": "Laura Martínez", "email": "laura@ejemplo.example",
                "telefono": "+34 600 000 099", "empresa": "Demo Corp"},
    "privacidad": "si", "publicidad": "no",
    "conversacion": [
        {"quien": "bot", "texto": "Hola, soy el asistente virtual de [EMPRESA]."},
        {"quien": "cliente", "texto": "Cena de empresa para 80 en el Mirador el 12 de diciembre. Somos de Demo Corp."},
        {"quien": "bot", "texto": "Para que el equipo prepare tu propuesta y se ponga en contacto contigo, necesito tu nombre y tu email."},
        {"quien": "cliente", "texto": "Laura Martínez, laura@ejemplo.example, mi móvil es +34 600 000 099."},
        {"quien": "bot", "texto": "Gracias, Laura. También puedes escribir a atencion@empresa-eventos.example o llamar al +34 930 000 000."},
    ],
    "resuelto_sin_humano": "si",
}


def caso(**cambios):
    d = copy.deepcopy(BASE)
    for k, v in cambios.items():
        if k in ("consulta", "cliente"):
            d[k].update(v)
        else:
            d[k] = v
    return d


resultados = []


def comprobar(nombre, ok, detalle=""):
    resultados.append(ok)
    print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
    if not ok and detalle:
        print(f"      {detalle}")


def personales_fuera(texto):
    return not any(x in texto for x in ("Laura", "laura@ejemplo.example", "600 000 099", "Demo Corp"))


# 1. Consulta completa, "sí" a la privacidad y "no" a la publicidad
r = procesar(caso(), registro=registro_nuevo())
p = r["payload"]
comprobar("1. consulta completa → 15 campos, gdpr yes, marketing no, 202_simulada",
          list(p) == CAMPOS and all(isinstance(v, str) for v in p.values())
          and p["gdpr_consent"] == "yes" and p["marketing_consent"] == "no"
          and r["respuesta"] == "202_simulada" and r["enviado"] == "simulado"
          and r["frase"] == FRASES["exito"]["es"], r)

# 2. Formato de lead_id y timestamp
comprobar("2. lead_id CB-AAAAMMDD-HHMMSS-XXXX y timestamp ISO 8601 UTC",
          re.fullmatch(r"CB-\d{8}-\d{6}-[A-Z0-9]{4}", p["lead_id"]) is not None
          and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", p["timestamp"]) is not None,
          f"{p['lead_id']} · {p['timestamp']}")

# 3. Espacio normalizado; solo zona → la zona
r3a = procesar(caso(id_conversacion="c3a", consulta={"espacio_elegido": "Llum"}), registro=registro_nuevo())
r3b = procesar(caso(id_conversacion="c3b", consulta={"espacio_elegido": "", "zona": "Poblenou"}), registro=registro_nuevo())
comprobar('3. "Llum" → "Llum del Poblenou"; solo zona → la zona',
          r3a["payload"]["preferred_location"] == "Llum del Poblenou"
          and r3b["payload"]["preferred_location"] == "Poblenou",
          f"{r3a['payload']['preferred_location']!r} · {r3b['payload']['preferred_location']!r}")

# 4. Fecha: solo día exacto
r4a = procesar(caso(id_conversacion="c4a", consulta={"fecha": "en marzo"}), registro=registro_nuevo())
r4b = procesar(caso(id_conversacion="c4b", consulta={"fecha": "2026-12-12"}), registro=registro_nuevo())
comprobar('4. "en marzo" → event_date ""; 2026-12-12 → se mantiene',
          r4a["payload"]["event_date"] == "" and r4b["payload"]["event_date"] == "2026-12-12")

# 5 y 6. Privacidad "no" y solo teléfono → sin datos personales
for n, priv in (("5", "no"), ("6", "solo_telefono")):
    r = procesar(caso(id_conversacion=f"c{n}", privacidad=priv, publicidad="si"), registro=registro_nuevo())
    p = r["payload"]
    comprobar(f"{n}. privacidad {priv} → campos personales vacíos, conversación tapada, consentimientos no, frase vacía",
              all(p[c] == "" for c in ("name", "email", "phone", "company"))
              and personales_fuera(p["conversation"]) and personales_fuera(p["message"])
              and "[nombre]" in p["conversation"] and "[email]" in p["conversation"]
              and "[teléfono]" in p["conversation"] and "[empresa]" in p["conversation"]
              and p["gdpr_consent"] == "no" and p["marketing_consent"] == "no"
              and r["frase"] == "" and r["enviado"] == "simulado"
              and "atencion@empresa-eventos.example" in p["conversation"],  # el contacto del equipo se queda
              p["conversation"])

# 7. Tarjeta, IBAN y DNI → tapados aunque haya consentimiento
conv7 = BASE["conversacion"] + [{"quien": "cliente", "texto":
        "Os paso mi tarjeta 4111 1111 1111 1111, mi IBAN ES91 2100 0418 4502 0005 1332 y mi DNI 12345678Z."}]
r = procesar(caso(id_conversacion="c7", conversacion=conv7,
                  consulta={"escalados": ["Tarjeta 4111-1111-1111-1111"]}), registro=registro_nuevo())
p = r["payload"]
comprobar("7. tarjeta, IBAN y DNI tapados con consentimiento",
          "[tarjeta]" in p["conversation"] and "[IBAN]" in p["conversation"] and "[DNI]" in p["conversation"]
          and "4111" not in p["conversation"] and "ES91" not in p["conversation"] and "12345678" not in p["conversation"]
          and "4111" not in p["message"] and "Laura Martínez" in p["conversation"],
          p["conversation"].splitlines()[-1])

# 8. La misma conversación dos veces → el segundo intento no envía
reg8 = registro_nuevo()
r8a = procesar(caso(id_conversacion="c8"), registro=reg8)
r8b = procesar(caso(id_conversacion="c8"), registro=reg8)
lineas8 = reg8.read_text(encoding="utf-8").splitlines()
comprobar("8. misma conversación dos veces → no se reenvía (mismo lead_id, una sola línea)",
          r8b.get("ya_enviado") is True and r8b["lead_id"] == r8a["lead_id"] and r8b["payload"] is None
          and len(lineas8) == 1, r8b)

# 9. Ruta incidencia → no envía y registra
reg9 = registro_nuevo()
r = procesar(caso(id_conversacion="c9", ruta="incidencia", decision="escalar_humano", motivo_escalado="queja"),
             registro=reg9)
linea9 = json.loads(reg9.read_text(encoding="utf-8"))
comprobar("9. ruta incidencia → no envía y registra",
          r["enviado"] == "no" and r["respuesta"] == "—" and r["payload"] is None
          and linea9["ruta"] == "incidencia" and linea9["enviado_n8n"] == "no" and linea9["motivo_escalado"] == "queja")

# 9b. Queja + evento nuevo (lead en rutas_adicionales) → sí envía
r = procesar(caso(id_conversacion="c9b", ruta="incidencia", rutas_adicionales=["lead"]), registro=registro_nuevo())
comprobar("9b. lead en rutas_adicionales → envía", r["enviado"] == "simulado")

# 10. Privacidad sin respuesta → no envía y registra
reg10 = registro_nuevo()
r = procesar(caso(id_conversacion="c10", privacidad="sin_respuesta"), registro=reg10)
linea10 = json.loads(reg10.read_text(encoding="utf-8"))
comprobar("10. privacidad sin respuesta → no envía y registra",
          r["enviado"] == "no" and r["payload"] is None and linea10["enviado_n8n"] == "no"
          and linea10["consentimiento_datos"] == "no")


# 11. Servidor local de prueba
class Servidor(BaseHTTPRequestHandler):
    modo, recibidos, clave = "202", [], None

    def do_POST(self):
        cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Servidor.recibidos.append({"lead_id": cuerpo["lead_id"], "clave": self.headers.get("X-API-Key"),
                                   "tipo": self.headers.get("Content-Type")})
        if Servidor.modo == "lento":
            time.sleep(1.0)
        codigo = 202 if Servidor.modo == "202" else 403 if Servidor.modo == "403" else 202
        try:
            self.send_response(codigo)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received", "lead_id": cuerpo["lead_id"]}).encode())
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), Servidor)
srv.daemon_threads = True
threading.Thread(target=srv.serve_forever, daemon=True).start()
url_local = "http://{}:{}/webhook/prueba".format(*srv.server_address)
clave_prueba = secrets.token_hex(8)  # aleatoria, solo para este test

for modo, nombre, esperado in (
        ("202", "11a. servidor local 202 → frase de éxito, una petición con X-API-Key", "202"),
        ("403", "11b. servidor local 403 → sin reintento, frase 'igualmente'", "403"),
        ("lento", "11c. sin respuesta → un único reintento con el mismo lead_id", "sin_respuesta")):
    Servidor.modo, Servidor.recibidos = modo, []
    r = procesar(caso(id_conversacion=f"c11-{modo}"), url=url_local, clave=clave_prueba,
                 registro=registro_nuevo(), timeout=0.3)
    time.sleep(0.1)
    rec = Servidor.recibidos
    if modo == "202":
        ok = (r["respuesta"] == "202" and r["enviado"] == "si" and r["frase"] == FRASES["exito"]["es"]
              and len(rec) == 1 and rec[0]["clave"] == clave_prueba and rec[0]["tipo"] == "application/json")
    elif modo == "403":
        ok = r["respuesta"] == "403" and len(rec) == 1 and r["frase"] == FRASES["error"]["es"]
    else:
        ok = (r["respuesta"] == "sin_respuesta" and len(rec) == 2
              and rec[0]["lead_id"] == rec[1]["lead_id"] == r["lead_id"] and r["frase"] == FRASES["error"]["es"])
    comprobar(nombre, ok, f"{r['respuesta']} · peticiones: {len(rec)}")
srv.shutdown()

# 12. Ningún registro contiene datos personales (ni la URL ni la clave)
todo = "".join(f.read_text(encoding="utf-8") for f in TMP.glob("*.jsonl"))
comprobar("12. ningún registro contiene nombre, email, teléfono, empresa, URL ni clave",
          personales_fuera(todo) and "laura" not in todo.lower() and url_local not in todo and clave_prueba not in todo
          and "conversation" not in todo)

print(f"\n{sum(resultados)}/{len(resultados)} casos correctos")
sys.exit(0 if all(resultados) else 1)
