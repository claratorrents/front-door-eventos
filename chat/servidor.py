#!/usr/bin/env python3
"""Servidor del chat web (solo biblioteca estándar).

Uso (desde la carpeta del proyecto):
    python3 chat/servidor.py            → http://127.0.0.1:8000

- Dirección: si existe la variable PORT (la pone Render), escucha en 0.0.0.0 y en ese puerto y
  entiende que está detrás de un proxy (la IP del cliente sale de X-Forwarded-For). Si no existe,
  solo en este ordenador: 127.0.0.1 y CHAT_PUERTO (por defecto 8000).
- La URL y la clave de n8n se leen de N8N_WEBHOOK_URL y N8N_API_KEY y no salen del servidor.
  Sin ellas, el envío se simula (202_simulada).
- El registro anónimo se escribe en registros/ de la carpeta desde la que se arranca.
- La media se sirve por id (/media/<id>), solo si está aprobada; el navegador nunca ve rutas.
- CORS (otro front en otra dirección): CHAT_CORS_ORIGIN con uno o varios orígenes exactos separados
  por comas. Solo se responde con Access-Control-Allow-Origin si el Origin de la petición está en la
  lista. Por defecto está vacía: sin CORS. Nunca "*".
- GET /health → {"ok": true} (para que el alojamiento sepa que está vivo).
- Límites: MAX_SESIONES conversaciones en memoria (se cierran las más antiguas) y
  LIMITE_PETICIONES_MINUTO peticiones a /api/ por IP (429 con una frase amable).
"""

import collections
import json
import os
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

CHAT = Path(__file__).resolve().parent
RAIZ = CHAT.parent
sys.path.insert(0, str(CHAT))
sys.path.insert(0, str(RAIZ / "scripts"))

import config  # noqa: E402
from conversacion import FRASES, Conversacion  # noqa: E402
from recomendar import cargar_espacios  # noqa: E402

ESTATICOS = {"/": ("index.html", "text/html; charset=utf-8"),
             "/static/chat.css": ("static/chat.css", "text/css; charset=utf-8"),
             "/static/chat.js": ("static/chat.js", "text/javascript; charset=utf-8")}
TIPOS_MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".svg": "image/svg+xml"}
CABECERAS = {"X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
             "Content-Security-Policy": "default-src 'self'; img-src 'self'; style-src 'self'; "
                                        "script-src 'self'; connect-src 'self'; frame-ancestors 'none'"}


def mapa_media():
    """id de media → archivo, solo fotos y planos aprobados que existen dentro de media/."""
    base = (RAIZ / "media").resolve()
    mapa = {}
    for esp in cargar_espacios():
        for m in esp.get("media", []):
            if m.get("approved") is True and m.get("type") in ("foto", "plano"):
                ruta = (RAIZ / m["url"].lstrip("/")).resolve()
                if base in ruta.parents and ruta.is_file() and ruta.suffix.lower() in TIPOS_MEDIA:
                    mapa[m["id"]] = ruta
                    en = ruta.with_name(ruta.stem + ".en" + ruta.suffix)   # plano en inglés (plano.en.svg)
                    if m["type"] == "plano" and en.is_file():
                        mapa[m["id"] + ".en"] = en
    return mapa


def leer_origenes(valor):
    """'https://a.com, https://b.com' → ['https://a.com', 'https://b.com']. Nunca '*'."""
    if not valor:
        return []
    if isinstance(valor, (list, tuple)):
        origenes = [str(v).strip() for v in valor]
    else:
        origenes = [v.strip() for v in str(valor).split(",")]
    origenes = [o.rstrip("/") for o in origenes if o]
    if "*" in origenes:
        raise ValueError('CHAT_CORS_ORIGIN no puede ser "*": pon las direcciones exactas del front, '
                         'p. ej. https://spaces.flowstate.digital')
    return origenes


def crear_servidor(host=config.HOST, puerto=config.PUERTO, url=None, clave=None, registro=None, hoy=None,
                   cors_origin=None, detras_de_proxy=False, max_sesiones=config.MAX_SESIONES,
                   limite_por_minuto=config.LIMITE_PETICIONES_MINUTO):
    sesiones, cerrojo = {}, threading.Lock()
    origenes = leer_origenes(cors_origin)
    peticiones = collections.defaultdict(collections.deque)   # IP → momentos de sus peticiones a /api/
    cerrojo_ip = threading.Lock()
    media = mapa_media()
    error_ui = FRASES["es"]["ui"]["error"]

    class Manejador(BaseHTTPRequestHandler):
        server_version = "chat-eventos"
        sys_version = ""

        def log_message(self, formato, *args):   # sin cuerpos ni datos del cliente en el log
            sys.stderr.write(f"{self.command} {urlparse(self.path).path} {args[1] if len(args) > 1 else ''}\n")

        def _enviar(self, codigo, cuerpo, tipo):
            datos = cuerpo if isinstance(cuerpo, bytes) else cuerpo.encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(datos)))
            self.send_header("Cache-Control", "no-store")
            for k, v in CABECERAS.items():
                self.send_header(k, v)
            self._cors()
            self.end_headers()
            self.wfile.write(datos)

        def _origen_permitido(self):
            origen = (self.headers.get("Origin") or "").rstrip("/")
            return origen if origen and origen in origenes else None

        def _cors(self):
            if origenes:   # solo si se ha configurado CHAT_CORS_ORIGIN (orígenes exactos, nunca "*")
                self.send_header("Vary", "Origin")
                permitido = self._origen_permitido()
                if permitido:
                    self.send_header("Access-Control-Allow-Origin", permitido)

        def do_OPTIONS(self):   # petición previa del navegador (CORS)
            if not origenes:
                return self._json(405, {"error": "no permitido"})
            if not self._origen_permitido():
                return self._json(403, {"error": "origen no permitido"})
            self.send_response(204)
            self._cors()
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _json(self, codigo, obj):
            self._enviar(codigo, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

        def _ip(self):
            if detras_de_proxy:   # detrás del proxy de Render: primer valor de X-Forwarded-For
                reenviada = (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
                if reenviada:
                    return reenviada
            return self.client_address[0]

        def _demasiadas(self):
            """True si esta IP ha superado el límite de peticiones a /api/ en el último minuto."""
            ahora, ip = time.time(), self._ip()
            with cerrojo_ip:
                cola = peticiones[ip]
                while cola and cola[0] < ahora - 60:
                    cola.popleft()
                if len(cola) >= limite_por_minuto:
                    return True
                cola.append(ahora)
                return False

        def do_GET(self):
            ruta = urlparse(self.path).path
            if ruta == "/health":
                return self._json(200, {"ok": True})
            if ruta in ESTATICOS:
                archivo, tipo = ESTATICOS[ruta]
                return self._enviar(200, (CHAT / archivo).read_bytes(), tipo)
            if ruta.startswith("/media/"):
                mid = ruta[len("/media/"):]
                if mid in media:
                    return self._enviar(200, media[mid].read_bytes(), TIPOS_MEDIA[media[mid].suffix.lower()])
            self._json(404, {"error": "no encontrado"})

        def do_POST(self):
            ruta = urlparse(self.path).path
            try:
                largo = int(self.headers.get("Content-Length") or 0)
                if largo > config.MAX_CUERPO:
                    return self._json(413, {"error": error_ui})
                cuerpo = json.loads(self.rfile.read(largo) or b"{}")
                if not isinstance(cuerpo, dict):
                    raise ValueError
            except (ValueError, json.JSONDecodeError):
                return self._json(400, {"error": error_ui})
            try:
                with cerrojo:
                    conv = sesiones.get(str(cuerpo.get("sesion", "")))
                if self._demasiadas():   # 429 con una frase amable en el idioma de la conversación
                    idioma = conv.idioma if conv else (cuerpo.get("idioma") if cuerpo.get("idioma") in config.IDIOMAS
                                                       else "es")
                    return self._json(429, {"error": FRASES[idioma]["demasiado_rapido"], "limite": True})
                if ruta == "/api/nueva":
                    sid = "conv-" + secrets.token_hex(8)
                    conv = Conversacion(sid, hoy=hoy, url=url, clave=clave, registro=registro)
                    salida = {"sesion": sid, "idioma": conv.idioma, "ui": conv.ui(), "mensajes": []}
                    if cuerpo.get("motivo") == "sesion_perdida":
                        # La conversación anterior ya no existe (p. ej. se reinició el servidor): se empieza
                        # otra en el mismo idioma; el aviso de IA ya se dio en la anterior
                        if cuerpo.get("idioma") in config.IDIOMAS:
                            conv.idioma = cuerpo["idioma"]
                        conv.aviso_dado = True
                        frase = conv.f("sesion_perdida")
                        conv.historial.append(("bot", frase))
                        salida.update(idioma=conv.idioma, ui=conv.ui(), mensajes=[{"tipo": "texto", "texto": frase}])
                    with cerrojo:
                        # Límite de conversaciones en memoria: se cierran (y registran) las más antiguas
                        while len(sesiones) >= max_sesiones:
                            antigua = min(sesiones, key=lambda s: sesiones[s].ultimo)
                            sesiones[antigua].cerrar_por_inactividad()
                            del sesiones[antigua]
                        sesiones[sid] = conv
                    return self._json(200, salida)
                if conv is None:   # sesión que ya no existe: el navegador empieza otra
                    return self._json(404, {"error": error_ui, "sesion_perdida": True})
                with cerrojo:
                    if ruta == "/api/mensaje":
                        formulario = cuerpo.get("formulario")
                        salida = conv.recibir(texto=cuerpo.get("texto"),
                                              accion=str(cuerpo["accion"]) if cuerpo.get("accion") else None,
                                              formulario=formulario if isinstance(formulario, dict) else None)
                    elif ruta == "/api/cerrar":
                        salida = conv.recibir(accion="terminar")
                    else:
                        return self._json(404, {"error": "no encontrado"})
                return self._json(200, salida)
            except Exception as e:  # noqa: BLE001 — al navegador, solo la frase de error (ni rutas ni trazas)
                sys.stderr.write(f"error: {type(e).__name__}: {e}\n")
                return self._json(500, {"error": error_ui})

    servidor = ThreadingHTTPServer((host, puerto), Manejador)
    servidor.daemon_threads = True
    servidor.sesiones = sesiones
    servidor.peticiones = peticiones

    def vigilar_inactividad():
        while True:
            time.sleep(60)
            limite = time.time() - config.INACTIVIDAD_MINUTOS * 60
            with cerrojo:
                for sid, conv in list(sesiones.items()):
                    if conv.ultimo < limite:
                        conv.cerrar_por_inactividad()     # registra la conversación (decisión 5)
                        del sesiones[sid]
            with cerrojo_ip:                              # olvida las IP sin peticiones en el último minuto
                for ip, cola in list(peticiones.items()):
                    if not cola or cola[-1] < time.time() - 60:
                        del peticiones[ip]

    threading.Thread(target=vigilar_inactividad, daemon=True).start()
    return servidor


def main():
    url, clave = os.environ.get("N8N_WEBHOOK_URL"), os.environ.get("N8N_API_KEY")
    if os.environ.get("PORT"):   # alojado (Render): escucha en la red, detrás de su proxy
        host, puerto, proxy = "0.0.0.0", int(os.environ["PORT"]), True
    else:                        # en local: solo este ordenador
        host, puerto, proxy = config.HOST, int(os.environ.get("CHAT_PUERTO", config.PUERTO)), False
    try:
        origenes = leer_origenes(os.environ.get("CHAT_CORS_ORIGIN"))
    except ValueError as e:
        sys.exit(str(e))
    servidor = crear_servidor(host, puerto, url=url, clave=clave, cors_origin=origenes, detras_de_proxy=proxy)
    modo = "envío real a n8n" if (url and clave) else "envío SIMULADO (sin N8N_WEBHOOK_URL / N8N_API_KEY)"
    print(f"Chat escuchando en {host}:{puerto} · {modo} · CORS: {', '.join(origenes) or 'no'} · "
          f"registro en {Path.cwd() / 'registros'}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
