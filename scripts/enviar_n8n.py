#!/usr/bin/env python3
"""Envía una consulta terminada a n8n (contrato de KNOWLEDGE.md §3.2) y apunta cada
conversación en el registro anónimo. Sigue la skill .claude/skills/envio-n8n/SKILL.md.

Solo biblioteca estándar. La URL y la clave salen SOLO de las variables de entorno
N8N_WEBHOOK_URL y N8N_API_KEY; sin ellas, el envío se simula (202_simulada). El script
nunca imprime ni guarda la URL ni la clave.

Uso:
  python3 scripts/enviar_n8n.py conversacion.json      (o el JSON por stdin)

Entrada (JSON):
  id_conversacion, idioma (es/ca/en), ruta, rutas_adicionales, decision, motivo_escalado,
  consulta {tipo_evento, asistentes, espacio_elegido, zona, fecha, presupuesto,
            necesidades, escalados: [frases]},
  cliente {nombre, email, telefono, empresa},
  privacidad (si/no/solo_telefono/sin_respuesta), publicidad (si/no/sin_respuesta),
  conversacion [{quien: bot|cliente, texto}], resuelto_sin_humano (si/no)

Salida (JSON): enviado (si/no/simulado), respuesta (202/202_simulada/403/404/
  sin_respuesta/—), lead_id, frase, payload (tapado) y, si ya se había enviado,
  ya_enviado: true.
Registro: una línea por conversación en registros/conversaciones.jsonl, sin datos personales.
"""

import datetime
import json
import os
import re
import secrets
import socket
import string
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESPACIOS = RAIZ / "data" / "espacios.json"
REGISTRO = RAIZ / "registros" / "conversaciones.jsonl"
TIMEOUT = 10  # segundos (contrato)

CAMPOS = ["lead_id", "timestamp", "name", "email", "company", "phone", "preferred_location",
          "event_type", "event_date", "guests", "budget_eur", "message", "conversation",
          "gdpr_consent", "marketing_consent"]

# Frases de la skill envio-n8n §4. El castellano es el texto del equipo; el catalán y el
# inglés son traducciones PROVISIONALES (pendientes de revisión del equipo).
FRASES = {
    "exito": {"es": "Gracias. El equipo se pondrá en contacto contigo en breve.",
              "ca": "Gràcies. L'equip es posarà en contacte amb tu aviat.",
              "en": "Thank you. The team will get in touch with you shortly."},
    "error": {"es": "No he podido enviar tu consulta. Escríbenos a atencion@empresa-eventos.example o llámanos al +34 930 000 000 (de lunes a sábado, de 9 a 18 h) y te atendemos.",
              "ca": "No he pogut enviar la teva consulta. Escriu-nos a atencion@empresa-eventos.example o "
                    "truca'ns al +34 930 000 000 (de dilluns a dissabte, de 9 a 18 h) i t'atendrem.",
              "en": "I couldn't send your enquiry. Email us at atencion@empresa-eventos.example or call us "
                    "on +34 930 000 000 (Monday to Saturday, 9 am to 6 pm) and we'll help you."},
}

# --- Tapado -------------------------------------------------------------------------
TARJETA = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")                 # 13-19 dígitos
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[ -]?[A-Z0-9]{4}){3,7}(?:[ -]?[A-Z0-9]{1,3})?\b")
DNI = re.compile(r"\b(?:\d{8}|[XYZ]\d{7})[ -]?[A-Z]\b", re.IGNORECASE)    # DNI y NIE
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
TELEFONO = re.compile(r"(?<![\w+])\+?\d(?:[ .-]?\d){8,11}(?!\w)")           # 9-12 dígitos


def tapar_siempre(texto):
    """Tarjetas, IBAN y DNI/NIE: se tapan siempre, haya o no consentimiento."""
    texto = IBAN.sub("[IBAN]", texto)
    texto = TARJETA.sub("[tarjeta]", texto)
    return DNI.sub("[DNI]", texto)


def tapar_personales(texto, cliente, generico):
    """Sin consentimiento: los datos del cliente → [nombre], [email], [teléfono], [empresa].
    generico=True tapa además cualquier email o teléfono (en las líneas del cliente y en
    message; en las del bot se deja el contacto del equipo)."""
    for clave, marca in (("email", "[email]"), ("telefono", "[teléfono]"),
                         ("empresa", "[empresa]"), ("nombre", "[nombre]")):
        valor = (cliente.get(clave) or "").strip()
        if valor:
            texto = re.sub(re.escape(valor), marca, texto, flags=re.IGNORECASE)
    nombre = (cliente.get("nombre") or "").strip()
    for parte in nombre.split():
        if len(parte) >= 3:  # "Laura" de "Laura Martínez" también se tapa
            texto = re.sub(rf"\b{re.escape(parte)}\b", "[nombre]", texto, flags=re.IGNORECASE)
    if generico:
        texto = EMAIL.sub("[email]", texto)
        texto = TELEFONO.sub("[teléfono]", texto)
    return texto


# --- Campos -------------------------------------------------------------------------
def _norm(texto):
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\b(el|la|els|les|l)\b", " ", t).split()


def normalizar_espacio(nombre, espacios=None):
    """'Llum' o 'el Mirador' → nombre completo del catálogo. Si no hay una coincidencia
    única, se deja el texto tal cual."""
    nombre = (nombre or "").strip()
    if not nombre:
        return ""
    if espacios is None:
        with open(ESPACIOS, encoding="utf-8") as f:
            espacios = json.load(f)["venues"]
    buscadas = _norm(nombre)
    coinciden = [e["name"] for e in espacios
                 if e["id"] == nombre or (buscadas and all(p in _norm(e["name"]) for p in buscadas))]
    return coinciden[0] if len(coinciden) == 1 else nombre


def fecha_exacta(fecha):
    """Solo un día exacto AAAA-MM-DD válido; cualquier otra cosa → ''."""
    fecha = (fecha or "").strip()
    try:
        return fecha if re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha) and datetime.date.fromisoformat(fecha) else ""
    except ValueError:
        return ""


def nuevo_lead_id(ahora):
    sufijo = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"CB-{ahora.strftime('%Y%m%d-%H%M%S')}-{sufijo}"


def _texto(v):
    return "" if v is None else str(v).strip()


def montar_payload(datos, ahora):
    consulta, cliente = datos.get("consulta", {}), datos.get("cliente", {})
    con_datos = datos.get("privacidad") == "si"
    gdpr = "yes" if con_datos else "no"
    marketing = "yes" if con_datos and datos.get("publicidad") == "si" else "no"

    frases = [_texto(consulta.get("necesidades"))] + [_texto(e) for e in consulta.get("escalados", [])]
    message = " ".join(f if f.endswith((".", "!", "?")) else f + "." for f in frases if f)
    message = tapar_siempre(message)

    lineas = []
    for turno in datos.get("conversacion", []):
        es_cliente = turno.get("quien") == "cliente"
        texto = tapar_siempre(_texto(turno.get("texto")))
        if not con_datos:
            texto = tapar_personales(texto, cliente, generico=es_cliente)
        lineas.append(f"{'Client' if es_cliente else 'Bot'}: {texto}")
    if not con_datos:
        message = tapar_personales(message, cliente, generico=True)

    espacio = normalizar_espacio(consulta.get("espacio_elegido"))
    payload = {
        "lead_id": nuevo_lead_id(ahora),
        "timestamp": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "name": _texto(cliente.get("nombre")) if con_datos else "",
        "email": _texto(cliente.get("email")) if con_datos else "",
        "company": _texto(cliente.get("empresa")) if con_datos else "",
        "phone": _texto(cliente.get("telefono")) if con_datos else "",
        "preferred_location": espacio or _texto(consulta.get("zona")),
        "event_type": _texto(consulta.get("tipo_evento")),
        "event_date": fecha_exacta(consulta.get("fecha")),
        "guests": _texto(consulta.get("asistentes")),
        "budget_eur": _texto(consulta.get("presupuesto")),
        "message": message,
        "conversation": "\n".join(lineas),
        "gdpr_consent": gdpr,
        "marketing_consent": marketing,
    }
    return {k: payload[k] for k in CAMPOS}, espacio


# --- Envío --------------------------------------------------------------------------
def _post(url, clave, payload, timeout):
    """Devuelve el código HTTP, o None si no hubo respuesta."""
    req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json", "X-API-Key": clave},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError):
        return None


def enviar(payload, url, clave, timeout=TIMEOUT):
    """Sin URL o clave → 202_simulada. Si no hay respuesta, un único reintento con el
    mismo payload (mismo lead_id). 403/404 → sin reintento."""
    if not url or not clave:
        return "202_simulada"
    codigo = _post(url, clave, payload, timeout)
    if codigo is None:
        codigo = _post(url, clave, payload, timeout)
    if codigo is None:
        print("n8n: sin respuesta tras el reintento", file=sys.stderr)
        return "sin_respuesta"
    if not 200 <= codigo < 300:
        print(f"n8n: respuesta {codigo}", file=sys.stderr)  # nunca la URL ni la clave
    return str(codigo)


# --- Registro -----------------------------------------------------------------------
def envio_anterior(id_conversacion, registro):
    """La línea del registro de un envío ya intentado de esta conversación, o None."""
    if not registro.exists():
        return None
    with open(registro, encoding="utf-8") as f:
        for linea in f:
            try:
                r = json.loads(linea)
            except json.JSONDecodeError:
                continue
            if r.get("id_conversacion") == id_conversacion and r.get("respuesta_n8n") not in (None, "—"):
                return r
    return None


def registrar(linea, registro):
    registro.parent.mkdir(parents=True, exist_ok=True)
    with open(registro, "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")


# --- Proceso ------------------------------------------------------------------------
def procesar(datos, url=None, clave=None, registro=REGISTRO, timeout=TIMEOUT, ahora=None):
    registro = Path(registro)
    ahora = ahora or datetime.datetime.now(datetime.timezone.utc)
    idioma = datos.get("idioma") if datos.get("idioma") in ("es", "ca", "en") else "es"

    # 2. No envía dos veces
    anterior = envio_anterior(datos.get("id_conversacion"), registro)
    if anterior:
        return {"enviado": anterior["enviado_n8n"], "respuesta": anterior["respuesta_n8n"],
                "lead_id": anterior["lead_id"], "frase": "", "payload": None, "ya_enviado": True}

    # 1. Decide si se envía
    es_lead = datos.get("ruta") == "lead" or "lead" in (datos.get("rutas_adicionales") or [])
    se_envia = es_lead and datos.get("privacidad") not in (None, "sin_respuesta")

    con_datos = datos.get("privacidad") == "si"
    resultado = {"enviado": "no", "respuesta": "—", "lead_id": "", "frase": "", "payload": None}
    espacio = normalizar_espacio(datos.get("consulta", {}).get("espacio_elegido"))
    if se_envia:
        payload, espacio = montar_payload(datos, ahora)
        respuesta = enviar(payload, url, clave, timeout)
        exito = respuesta == "202_simulada" or respuesta.startswith("2")
        frase = "" if not con_datos else FRASES["exito" if exito else "error"][idioma]
        resultado = {"enviado": "simulado" if respuesta == "202_simulada" else ("si" if exito else "no"),
                     "respuesta": respuesta, "lead_id": payload["lead_id"], "frase": frase,
                     "payload": payload}

    # 7. Registro anónimo (campos de KNOWLEDGE §3.2, decisión 11)
    registrar({
        "id_conversacion": datos.get("id_conversacion", ""),
        "fecha_hora": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "idioma": idioma,
        "ruta": datos.get("ruta", ""),
        "rutas_adicionales": datos.get("rutas_adicionales") or [],
        "decision": datos.get("decision") or "ninguna",
        "motivo_escalado": datos.get("motivo_escalado") or "—",
        "espacio_elegido": espacio,
        "enviado_n8n": resultado["enviado"],
        "respuesta_n8n": resultado["respuesta"],
        "lead_id": resultado["lead_id"],
        "consentimiento_datos": "si" if con_datos else "no",
        "consentimiento_publicidad": "si" if con_datos and datos.get("publicidad") == "si" else "no",
        "resuelto_sin_humano": datos.get("resuelto_sin_humano", "no"),
    }, registro)
    return resultado


def main():
    texto = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
    datos = json.loads(texto)
    r = procesar(datos, url=os.environ.get("N8N_WEBHOOK_URL"), clave=os.environ.get("N8N_API_KEY"))
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
