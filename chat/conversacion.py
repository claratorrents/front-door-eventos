"""Estado de una conversación del chat web y orden de los pasos.

No duplica la lógica de las skills: entiende el mensaje con entender_reglas.py y decide con
los scripts que ya existen:
  router.enrutar            qué intención va primero, ruta, a_n8n y acción
  recomendar.recomendar     espacios (con zona), validar_espacio y media_aprobada
  datos_consulta            qué falta preguntar y si está lista para enviar
  enviar_n8n.procesar       envío a n8n (simulado sin variables de entorno) y registro anónimo
Las frases salen de chat/frases.json; [EMPRESA], de chat/config.py.
"""

import copy
import datetime
import json
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402
from datos_consulta import datos_consulta  # noqa: E402
from entender_reglas import entender  # noqa: E402
from enviar_n8n import EMAIL, procesar  # noqa: E402
from recomendar import cargar_espacios, media_aprobada, recomendar, validar_espacio  # noqa: E402
from router import enrutar  # noqa: E402

FRASES = json.loads((Path(__file__).resolve().parent / "frases.json").read_text(encoding="utf-8"))
GRAVEDAD = {None: 0, "ninguna": 0, "escalar_comercial": 1, "pendiente_confirmar": 2, "escalar_humano": 3}
DATOS_CONSULTA = ("tipo", "asistentes", "espacio", "fecha_nivel", "presupuesto", "necesidades", "sin_necesidades")


class Respuesta:
    """Lo que el chatbot contesta en un turno. Como mucho dos preguntas por mensaje (router §3)."""

    def __init__(self):
        self.mensajes, self.cola, self.botones = [], [], []
        self.formulario = False
        self.n_preguntas = 0
        self.otro_tema = False       # se ha atendido otro tema antes de volver a la consulta
        self.preguntadas = []        # datos de datos_consulta preguntados en este turno
        self.pregunto_privacidad = False

    def texto(self, t):
        if t:
            self.mensajes.append({"tipo": "texto", "texto": t})

    def pregunta_ya(self, t, n=1):
        """Pregunta que va en su sitio (p. ej. confirmar la disposición antes de las tarjetas)."""
        self.texto(t)
        self.n_preguntas += n

    def pregunta(self, t, n=1, claves=(), botones=None, privacidad=False):
        self.cola.append({"texto": t, "n": n, "claves": list(claves), "botones": botones, "privacidad": privacidad})

    def bloque(self, b):
        self.mensajes.append(b)


class Conversacion:
    def __init__(self, id_conversacion, hoy=None, url=None, clave=None, registro=None, espacios=None):
        self.id = id_conversacion
        self.hoy = hoy or datetime.date.today()
        self.url, self.clave = url, clave           # solo en el servidor; nunca van al navegador
        self.registro = registro                    # None: registros/ del directorio de trabajo
        self.espacios = {e["id"]: e for e in (espacios or cargar_espacios())}
        self.idioma = "es"
        self.aviso_dado = False
        self.cerrada = False
        self.intenciones = []
        self.decision, self.motivo = None, None
        self.legal = False
        self._repetir_privacidad = False
        self._motivo_oferta = "peticion_humano"
        self.c = {"tipo": None, "tipo_base": None, "event_type": None, "disposicion": None, "disp_preguntada": False,
                  "tarde": False, "corporativo": False, "asistentes": None, "asistentes_texto": None, "zona": None,
                  "espacio": None, "fecha_nivel": "nada", "fecha": None, "hora_fin": None, "hora_ambigua": None,
                  "presupuesto": None, "necesidades": None, "sin_necesidades": False}
        self.escalados = []
        self.preguntados, self.respondidos, self.ultimas = [], [], []
        self.recomendados, self.recomendado = [], False
        self.validado = None
        self.consulta_activa = False
        self.fase = None              # privacidad, formulario, publicidad, oferta_envio, oferta_fotos, enviado
        self.priv_veces = 0
        self.privacidad, self.publicidad = "sin_respuesta", "sin_respuesta"
        self.cliente = {}
        self.no_entendidos, self.ofensas = 0, 0
        self.fotos_de = None
        self.historial = []
        self.resultado_envio = None
        self.registrada = False
        self.ultimo = time.time()

    # --- Frases -----------------------------------------------------------------------
    def f(self, clave, **huecos):
        t = FRASES[self.idioma][clave]
        for k, v in list(huecos.items()):
            if isinstance(v, str) and v:
                huecos[k[:1].upper() + k[1:]] = v[:1].upper() + v[1:]
        return t.format_map(huecos).replace("[EMPRESA]", config.EMPRESA)

    def pieza(self, grupo, clave):
        return FRASES[self.idioma][grupo].get(clave, clave)

    def ui(self):
        return {k: v.replace("[EMPRESA]", config.EMPRESA) for k, v in FRASES[self.idioma]["ui"].items()}

    def nombre(self, eid):
        """Español: 'el Llum' (articulo + nombre_corto). Inglés: el nombre completo, sin artículo."""
        e = self.espacios[eid]
        return f"{e['articulo']} {e['nombre_corto']}" if self.idioma == "es" else e["name"]

    # --- Estado -----------------------------------------------------------------------
    def _decidir(self, decision, motivo):
        if GRAVEDAD[decision] >= GRAVEDAD[self.decision]:
            self.decision, self.motivo = decision, motivo

    def _dias(self):
        if self.c["fecha_nivel"] == "dia" and self.c["fecha"]:
            return (datetime.date.fromisoformat(self.c["fecha"]) - self.hoy).days
        return None

    def _router(self, consulta_en_marcha=False):
        intenciones = self.intenciones or ["fuera_tema"]
        return enrutar(intenciones, legal=self.legal, consulta_en_marcha=consulta_en_marcha)

    # --- Entrada ----------------------------------------------------------------------
    def recibir(self, texto=None, accion=None, formulario=None):
        r = Respuesta()
        if self.cerrada:
            return self._salida(r)
        self.ultimo = time.time()
        if accion:
            return self._accion(accion, r)
        if formulario is not None:
            return self._formulario(formulario, r)
        texto = (texto or "").strip()[:config.MAX_TEXTO]
        if not texto:
            return self._salida(r)
        self.historial.append(("cliente", texto))
        e = entender(texto, {"idioma": self.idioma, "hoy": self.hoy, "esperando": self.ultimas})
        if e["idioma"] and (not self.aviso_dado or len(texto.split()) >= 2):
            self.idioma = e["idioma"]
        if not self.aviso_dado:
            r.texto(self.f("aviso"))
            self.aviso_dado = True
        s, d = e["senales"], e["datos"]

        if s.get("sensible"):
            r.texto(self.f("tarjeta" if s["sensible"] == "tarjeta" else "sensible"))
        if s.get("ofensivo"):
            self.ofensas += 1
            if self.ofensas == 1:
                r.texto(self.f("ofensivo_1"))
                r.n_preguntas += 1
                return self._salida(r)
            r.texto(self.f("ofensivo_2"))
            self._decidir("escalar_humano", "ofensivo")
            return self._cerrar(r, sin_envio=True, despedida=False)
        if not e["entendido"]:
            self.no_entendidos += 1
            r.texto(self.f("no_entendido" if self.no_entendidos == 1 else "no_entendido_2"))
            return self._salida(r)
        self.no_entendidos = 0

        # Despedida: una frase, sin preguntas ni botones; no cierra la conversación (decisión del 9/11)
        if e.get("despedida"):
            r.texto(self.f("despedida_cliente"))
            return self._salida(r, sin_repetir=True)

        for i in e["intenciones"]:
            if i == "informacion" and self.consulta_activa:
                continue                       # información dentro de un evento: no cambia la ruta
            if i not in self.intenciones:
                self.intenciones.append(i)
            if i == "queja":
                self.legal = e["legal"]

        if self._fase(e, texto, r):
            return self._salida(r)

        ints = e["intenciones"]
        # Inyección: si pide confirmar la reserva, B4; si además pide el prompt, la 23 sin su pregunta
        if s.get("confirmar_reserva"):
            r.texto(self.f("confirmar_reserva"))
            r.otro_tema = True
        if s.get("pide_prompt") or (s.get("inyeccion") and not s.get("confirmar_reserva")):
            if self.consulta_activa or s.get("confirmar_reserva"):
                r.texto(self.f("prompt").split("?")[0].rsplit(".", 1)[0] + ".")
            else:
                r.pregunta_ya(self.f("prompt"))
            r.otro_tema = True
        if "privacidad" in ints:
            if s.get("retirar_email") and self.consulta_activa and self.fase != "enviado":
                r.texto(self.f("retirar"))
                self.privacidad = "no"
                self.cliente = {}
            else:
                r.texto(self.f("borrar"))
                self._decidir("escalar_humano", "privacidad")
            r.otro_tema = True
        if "queja" in ints:
            r.texto(self.f("queja"))
            self._decidir("escalar_humano", "legal" if e["legal"] else "queja")
            r.otro_tema = True
        if "cambio_reserva" in ints:
            r.texto(self.f("persona_sin_consulta"))
            self._decidir("escalar_humano", "cambio_reserva")
            r.otro_tema = True
        if "persona" in ints or s.get("frustracion"):
            motivo = "frustracion" if s.get("frustracion") and "persona" not in ints else "peticion_humano"
            if self.consulta_activa and self.fase not in ("enviado",):
                prefijo = self.f("frustracion_prefijo") + " " if motivo == "frustracion" else ""
                ui = self.ui()
                r.pregunta_ya(prefijo + self.f("persona_con_consulta"))
                r.botones = [{"texto": ui["oferta_si"], "accion": "oferta:si"},
                             {"texto": ui["oferta_no"], "accion": "oferta:no"}]
                self.fase = "oferta_envio"
                self._motivo_oferta = motivo
                self._decidir("escalar_humano", motivo)
                return self._salida(r)
            r.texto(self.f("persona_sin_consulta"))
            self._decidir("escalar_humano", motivo)
            r.otro_tema = True
        if "fuera_tema" in ints and len(ints) == 1:
            r.pregunta_ya(self.f("fuera_tema"))
            return self._salida(r)
        if "nuevo_evento" in ints:
            self.consulta_activa = True

        # Guardrails dentro de la conversación
        if s.get("precio"):
            r.texto(self.f("precio"))
            r.otro_tema = True
        if s.get("disponibilidad"):
            r.texto(self.f("disponibilidad"))
            r.otro_tema = True
        if s.get("descuento"):
            r.texto(self.f("descuento"))
            pct = s["descuento"]
            self._escalado(f"Pide un {pct} % de descuento" if pct is not True else "Pide un descuento")
            self._decidir("escalar_comercial", "descuento")
            r.otro_tema = True
        if s.get("info"):
            self._info(s["info"], d, r)
        if s.get("media"):
            self._media(s["media"], d, r)
        if d.get("email") and self.fase not in ("privacidad", "formulario"):
            r.texto(self.f("email_antes"))

        # Datos de un evento sin intención clara ("somos unos 80…"): se abre la consulta
        claves_evento = ("tipo", "asistentes", "zona", "fecha_nivel") if (s.get("info") or s.get("media")) \
            else ("tipo", "asistentes", "espacio", "zona", "fecha_nivel")   # preguntar por un espacio no es un evento
        if not self.consulta_activa and self.fase is None and any(d.get(k) for k in claves_evento) and not (
                set(ints) & {"queja", "privacidad", "cambio_reserva", "persona"}):
            self.consulta_activa = True
            if "nuevo_evento" not in self.intenciones:
                self.intenciones.append("nuevo_evento")

        if self.fase == "enviado":
            if any(k in d for k in DATOS_CONSULTA):
                r.texto(self.f("ya_enviada_cambio"))
            elif re.search(r"reenv|resend|send it again", texto.lower()):
                r.texto(self.f("ya_enviada_reenvio"))
        elif self.consulta_activa:
            self._consulta(e, r)
        elif e["saludo"]:
            r.pregunta(self.f("que_evento"))
        # Nunca se queda callado: si no hay nada que decir, "no te he entendido" (B2)
        if not r.cola and all(m.get("texto") == self.f("aviso") for m in r.mensajes) and not r.botones \
                and not r.formulario:
            self.no_entendidos += 1
            r.texto(self.f("no_entendido" if self.no_entendidos == 1 else "no_entendido_2"))
        return self._salida(r)

    def _escalado(self, frase):
        if frase not in self.escalados:
            self.escalados.append(frase)

    # --- Fases que esperan una respuesta concreta --------------------------------------
    def _fase(self, e, texto, r):
        si_no, d = e["si_no"], e["datos"]
        if self.fase == "privacidad":
            solo_tel = d.get("telefono") and not d.get("email") and re.search(
                r"\b(email|correo|e-mail)\b", texto.lower()) and si_no != "si"
            if solo_tel:
                self.privacidad = "solo_telefono"
                r.texto(self.f("solo_telefono"))
                self._enviar(r)
                return True
            if si_no == "si":
                return self._abrir_formulario(r)
            if si_no == "no":
                return self._privacidad_no(r)
            self._repetir_privacidad = True
            return False
        if self.fase == "formulario":
            if si_no == "si":
                return self._abrir_formulario(r)
            r.formulario = True
            return False
        if self.fase == "publicidad":
            if si_no in ("si", "no"):
                self.publicidad = si_no
                self._enviar(r)
                return True
            self.publicidad = "no"          # no contesta: marketing_consent no (consentimiento §5)
            self._enviar(r)
            return False
        if self.fase == "oferta_envio":
            if si_no == "si":
                return self._aceptar_oferta(r)
            if si_no == "no":
                self.fase = None
                return False
            self.fase = None
            return False
        if self.fase == "oferta_alternativas":
            self.fase = None
            if si_no == "si":
                self._mostrar_alternativas(getattr(self, "_alternativas", []), r)
                return True
            return False
        if self.fase == "oferta_fotos":
            self.fase = None
            if si_no == "si" and self.fotos_de:
                self._galeria(self.fotos_de, r)
                if self.consulta_activa:     # y sigue la consulta (p. ej. la privacidad pendiente)
                    self._consulta({"datos": {}, "no_lo_sabe": False, "senales": {}}, r)
                return True
        return False

    def _abrir_formulario(self, r):
        r.texto(self.f("formulario_intro"))
        r.formulario = True
        self.fase = "formulario"
        return True

    def _privacidad_no(self, r):
        self.privacidad = "no"
        self.cliente = {}
        r.texto(self.f("privacidad_no"))
        self._enviar(r)
        return True

    def _aceptar_oferta(self, r):
        self._escalado("Pidió hablar con una persona" if getattr(self, "_motivo_oferta", "") != "frustracion"
                       else "Mostró frustración")
        self.fase = None
        self._preguntar_privacidad(r)
        return True

    def _preguntar_privacidad(self, r, prefijo=""):
        ui = self.ui()
        clave = "privacidad_empresa" if self.c["corporativo"] else "privacidad"
        r.pregunta(prefijo + self.f(clave), privacidad=True,
                   botones=[{"texto": ui["privacidad_si"], "accion": "privacidad:si"},
                            {"texto": ui["privacidad_no"], "accion": "privacidad:no"}])

    # --- Botones y formulario -----------------------------------------------------------
    def _accion(self, accion, r):
        tipo, _, valor = accion.partition(":")
        ui = self.ui()
        if tipo == "terminar":
            self.historial.append(("cliente", ui["terminar"]))
            return self._cerrar(r)
        if tipo in ("elegir", "plano", "fotos") and valor not in self.espacios:
            return self._salida(r)
        if tipo == "elegir":
            self.historial.append(("cliente", self.espacios[valor]["name"]))
            self.c["espacio"] = valor
            self.consulta_activa = True
            if "nuevo_evento" not in self.intenciones:
                self.intenciones.append("nuevo_evento")
            self._consulta({"datos": {}, "no_lo_sabe": False, "senales": {}}, r, eligio=True)
        elif tipo == "plano":
            self.historial.append(("cliente", f"{ui['ver_plano']} · {self.espacios[valor]['name']}"))
            self._plano(valor, r)
        elif tipo == "fotos":
            self.historial.append(("cliente", f"{ui['ver_fotos']} · {self.espacios[valor]['name']}"))
            self._galeria(valor, r)
        elif tipo == "privacidad" and self.fase in ("privacidad", "formulario", None) and self.privacidad == "sin_respuesta":
            self.historial.append(("cliente", ui["privacidad_si" if valor == "si" else "privacidad_no"]))
            if valor == "si":
                self._abrir_formulario(r)
            else:
                self._privacidad_no(r)
        elif tipo == "publicidad" and self.fase == "publicidad":
            self.historial.append(("cliente", ui["publicidad_si" if valor == "si" else "publicidad_no"]))
            self.publicidad = "si" if valor == "si" else "no"
            self._enviar(r)
        elif tipo == "oferta" and self.fase == "oferta_envio":
            self.historial.append(("cliente", ui["oferta_si" if valor == "si" else "oferta_no"]))
            if valor == "si":
                self._aceptar_oferta(r)
            else:
                self.fase = None
                self._consulta({"datos": {}, "no_lo_sabe": False, "senales": {}}, r)
        return self._salida(r)

    def _formulario(self, campos, r):
        if self.fase not in ("formulario", "privacidad") or self.privacidad != "sin_respuesta":
            return self._salida(r)
        limpio = {k: str(campos.get(k) or "").strip()[:200] for k in ("nombre", "email", "empresa", "telefono")}
        faltan = []
        if not limpio["nombre"]:
            faltan.append(self.pieza("faltas", "nombre"))
        if not EMAIL.fullmatch(limpio["email"]):
            faltan.append(self.pieza("faltas", "email"))
        if faltan:
            r.texto(self.f("falta_dato", falta=self.pieza("faltas", "y").join(faltan)))
            r.formulario = True
            self.fase = "formulario"
            return self._salida(r)
        self.cliente = limpio
        etiquetas = FRASES[self.idioma]["campos_linea"]
        linea = " · ".join(f"{etiquetas[k]}: {v}" for k, v in limpio.items() if v)
        self.historial.append(("cliente", linea))
        self.privacidad = "si"
        if limpio["empresa"]:
            self.c["corporativo"] = True
        ui = self.ui()
        r.pregunta(self.f("publicidad"), botones=[{"texto": ui["publicidad_si"], "accion": "publicidad:si"},
                                                 {"texto": ui["publicidad_no"], "accion": "publicidad:no"}])
        self.fase = "publicidad"
        return self._salida(r)

    # --- Consulta de evento -------------------------------------------------------------
    def _consulta(self, e, r, eligio=False):
        c, d = self.c, e["datos"]
        nuevo_dato = False
        if d.get("tipo") and d.get("tipo_base") != c["tipo_base"]:
            c.update(tipo=d["tipo"], tipo_base=d["tipo_base"], event_type=d.get("event_type"),
                     tarde=d.get("tarde", False), disposicion=d.get("disposicion"))
            nuevo_dato = True
        if d.get("corporativo"):
            c["corporativo"] = True
        if d.get("asistentes"):
            c["asistentes"], c["asistentes_texto"] = d["asistentes"], d["asistentes_texto"]
            nuevo_dato = True
        if d.get("zona"):
            c["zona"] = d["zona"]
        if d.get("espacio") and not e["senales"].get("info") and not e["senales"].get("media"):
            c["espacio"] = d["espacio"]
        if d.get("fecha_nivel"):
            if d.get("fecha_pasada"):
                r.pregunta(self.f("fecha_pasada"))
                return
            c["fecha_nivel"], c["fecha"] = d["fecha_nivel"], d.get("fecha")
        if d.get("hora_fin"):
            c["hora_fin"], c["hora_ambigua"] = d["hora_fin"], None
        elif d.get("hora_ambigua"):
            c["hora_ambigua"] = d["hora_ambigua"]
        elif c["hora_ambigua"] and e.get("si_no") == "si":
            c["hora_fin"], c["hora_ambigua"] = f"{(c['hora_ambigua'] % 12) + 12:02d}:00", None
        if d.get("presupuesto"):
            c["presupuesto"] = d["presupuesto"]
            nuevo_dato = True
        if d.get("necesidades"):
            c["necesidades"] = d["necesidades"]
            nuevo_dato = True
        if d.get("sin_necesidades"):
            c["sin_necesidades"] = True
            if "necesidades" not in self.respondidos:
                self.respondidos.append("necesidades")
        if e.get("no_lo_sabe"):
            for k in self.ultimas:
                if k not in self.respondidos:
                    self.respondidos.append(k)

        if c["hora_ambigua"] and not c["hora_fin"]:
            r.pregunta(self.f("hora_ambigua", h=str(c["hora_ambigua"])))
            return

        # 1. Recomendador: lo que necesita para recomendar (router §3)
        if not self.recomendado and not self.validado:
            if not c["tipo"] and not c["asistentes"]:
                r.pregunta(self.f("tipo_y_asistentes"), n=2, claves=["tipo", "asistentes"])
                return
            if not c["asistentes"]:
                r.pregunta(self.f("solo_asistentes"), claves=["asistentes"])
                return
            if not c["tipo"] or not c["disposicion"]:
                r.pregunta(self.f("solo_tipo"), claves=["tipo"])
                return
            if c["tarde"] and not c["hora_fin"]:
                if not c["disp_preguntada"]:
                    r.pregunta_ya(self._confirmar_disposicion())
                    c["disp_preguntada"] = True
                r.pregunta(self.f("hora_fin"))
                return
            if c["espacio"]:
                self._validar(r)
            else:
                self._recomendar(r)
        elif c["espacio"] and self.validado != (c["espacio"], c["fecha"], c["hora_fin"]):
            self._validar(r, eligio=eligio)
        elif nuevo_dato and not r.mensajes:
            r.texto(self.f("apuntado"))
        elif nuevo_dato:
            r.texto(self.f("apuntado"))

        # 2. Cualificador: lo que falta (datos_consulta.py)
        if self.fase in ("privacidad", "formulario", "publicidad", "oferta_envio", "oferta_alternativas", "enviado"):
            return
        espacio_nombre = self.espacios[c["espacio"]]["name"] if c["espacio"] else None
        dc = datos_consulta(tipo=c["tipo"], asistentes=c["asistentes_texto"], espacio=espacio_nombre, zona=c["zona"],
                            fecha=c["fecha_nivel"], presupuesto=c["presupuesto"],
                            necesidades=c["necesidades"] or ("—" if c["sin_necesidades"] else None),
                            preguntados=self.preguntados, respondidos=self.respondidos)
        if dc["listo_para_enviar"]:
            if self.privacidad == "sin_respuesta" and self.priv_veces == 0:
                self._preguntar_privacidad(r)
            return
        claves = list(dc["siguientes_preguntas"])
        if "espacio_o_zona" in claves and not self.recomendados:
            claves.remove("espacio_o_zona")
        self._preguntar_datos(claves, r)

    def _preguntar_datos(self, claves, r):
        if set(claves) == {"tipo", "asistentes"}:
            r.pregunta(self.f("tipo_y_asistentes"), n=2, claves=claves)
            return
        if claves == ["dia_exacto", "presupuesto"]:
            r.pregunta(self.f("dia_y_presupuesto"), n=2, claves=claves)
            return
        textos = {"tipo": "solo_tipo", "asistentes": "solo_asistentes", "espacio_o_zona": "pregunta_final",
                  "fecha": "fecha", "dia_exacto": "dia", "presupuesto": "presupuesto", "necesidades": "necesidades"}
        for k in claves:
            r.pregunta(self.f(textos[k]), claves=[k])

    def _confirmar_disposicion(self):
        c = self.c
        return self.f("confirmar_disposicion", un_tipo=self.pieza("un_tipo", c["tipo_base"]),
                      disposicion=self.pieza("disposiciones", c["disposicion"]))

    def _recomendar(self, r):
        c = self.c
        res = recomendar(c["asistentes"], c["disposicion"], self._dias(), c["hora_fin"], zona=c["zona"])
        recs = res["recomendados"]
        self.recomendado = True
        if not c["disp_preguntada"]:
            r.pregunta_ya(self._confirmar_disposicion())
            c["disp_preguntada"] = True
        if not recs:
            antelacion = any(x["motivo"] == "antelacion" for x in res["descartados"])
            disp = self.pieza("disposiciones", c["disposicion"])
            if antelacion:
                r.texto(self.f("sin_espacio_antelacion"))
                self._escalado("Fecha con menos antelación de la necesaria")
            else:
                r.texto(self.f("sin_espacio_aforo", n=str(c["asistentes"]), disposicion=disp))
                self._escalado(f"Ningún espacio tiene aforo para {c['asistentes']} en {FRASES['es']['disposiciones'][c['disposicion']]}")
            self._decidir("escalar_comercial", "excepcion")
            return
        self.recomendados = [x["id"] for x in recs]
        zona = c["zona"]
        en_zona = [x for x in recs if not x.get("otra_zona")]
        otras = [x for x in recs if x.get("otra_zona")]
        r.texto(self.f("intro_tarjetas"))
        if zona and not en_zona:
            r.texto(self.f("zona_ninguna", zona=zona))
            self._tarjetas(otras, recs, r)
        elif zona and len(en_zona) == 1 and en_zona[0]["grupo"] == "bajo_60" and any(x["grupo"] == "comodo" for x in otras):
            r.texto(self.f("zona_amplio", zona=zona, espacio=self.nombre(en_zona[0]["id"]), n=str(c["asistentes"])))
            mejor = next(x for x in otras if x["grupo"] == "comodo")
            self._tarjetas(en_zona + [mejor], recs, r)
            self.recomendados = [en_zona[0]["id"], mejor["id"]]
        else:
            self._tarjetas(en_zona if zona else recs, recs, r)
            if zona and otras:
                r.texto(self.f("zona_otras", zona=zona))
                self._tarjetas(otras, recs, r)
        for x in res["descartados"]:
            r.texto(self._descarte(x))
        r.pregunta(self.f("pregunta_final"), claves=[] if (zona or c["espacio"]) else ["espacio_o_zona"])

    def _descarte(self, x):
        if x["id"] == "sp-jardi-gracia" and x["motivo"] == "horario":
            return self.f("descarte_jardi")
        e = self.espacios[x["id"]]
        if x["motivo"] == "antelacion":
            return self.f("descarte_antelacion", espacio=self.nombre(x["id"]),
                          dias=str(e["chatbot_guardrails"]["min_lead_time_days"]))
        return self.f("descarte_horario", espacio=self.nombre(x["id"]), hora=e["chatbot_guardrails"]["max_end_time"])

    def _tarjetas(self, items, todos, r):
        c = self.c
        tarjetas = []
        principales = [x for x in todos if x["grupo"] != "bajo_60" or not x["alternativa"]]
        solo_bajos = all(x["grupo"] == "bajo_60" for x in todos)
        for x in items:
            e = self.espacios[x["id"]]
            disp = self.pieza("disposiciones", c["disposicion"])
            aforo = str(e["capacities"][c["disposicion"]])
            lineas = []
            if self.idioma == "es":
                lineas.append(e["tagline"] + ".")
            if c["event_type"] and c["event_type"] in e.get("event_types", []):
                lineas.append(self.f("tarjeta_aforo_tipo", n=aforo, disposicion=disp,
                                     tipos=self.pieza("tipos_plural", c["event_type"])))
            else:
                lineas.append(self.f("tarjeta_aforo", n=aforo, disposicion=disp))
            for a in x.get("avisos_zona", []):
                lineas.append(self.f("aviso_zona", hasta_general=e["chatbot_guardrails"]["max_end_time"],
                                     zona=self.pieza("zonas", a["zona"]), hasta=a["hasta"]))
            if x["grupo"] == "al_limite":
                otros = [y for y in principales if y["id"] != x["id"] and not y["alternativa"]]
                alternativa = next((y for y in todos if y["alternativa"]), None)
                if todos.index(x) > 0 and otros:
                    lineas.append(self.f("al_limite_otra", primera=self.nombre(todos[0]["id"])))
                elif alternativa:
                    lineas.append(self.f("al_limite_alternativa", alternativa=self.nombre(alternativa["id"]),
                                         n=str(self.espacios[alternativa["id"]]["capacities"][c["disposicion"]])))
                else:
                    lineas.append(self.f("al_limite_sola"))
            elif x["grupo"] == "bajo_60" and solo_bajos and (c["hora_fin"] or c["fecha_nivel"] == "dia"):
                lineas.append(self.f("bajo_60", motivo=self.pieza("motivos_amplio", "horario" if c["hora_fin"] else "fecha")))
            tarjetas.append(self._tarjeta(x["id"], lineas, x.get("foto")))
        r.bloque({"tipo": "tarjetas", "tarjetas": tarjetas})

    def _tarjeta(self, eid, lineas, foto, botones=True):
        e, ui = self.espacios[eid], self.ui()
        t = {"id": eid, "nombre": e["name"], "lineas": lineas, "botones": []}
        if foto:
            pie = [foto["description"], self.f("pie_foto")] if self.idioma == "es" else [self.f("pie_foto")]
            t["foto"] = {"url": f"/media/{foto['id']}", "alt": ui["alt_foto"].format(nombre=e["name"]), "pie": pie}
        if botones:
            t["botones"] = [{"texto": ui["ver_plano"], "accion": f"plano:{eid}"},
                            {"texto": ui["ver_fotos"], "accion": f"fotos:{eid}"},
                            {"texto": ui["elegir"], "accion": f"elegir:{eid}"}]
        return t

    def _validar(self, r, eligio=False):
        c = self.c
        primera = self.validado is None
        res = validar_espacio(c["espacio"], c["asistentes"], c["disposicion"], self._dias(), c["hora_fin"], zona=c["zona"])
        if res["encaja"]:
            if primera:
                r.texto(self.f("elegido", espacio=self.nombre(c["espacio"])))
                if c["espacio"] not in self.recomendados:   # eligió sin ver tarjetas: se enseña la suya
                    lineas = [self.espacios[c["espacio"]]["tagline"] + "."] if self.idioma == "es" else []
                    e = self.espacios[c["espacio"]]
                    disp = self.pieza("disposiciones", c["disposicion"])
                    aforo = str(e["capacities"][c["disposicion"]])
                    if c["event_type"] and c["event_type"] in e.get("event_types", []):
                        lineas.append(self.f("tarjeta_aforo_tipo", n=aforo, disposicion=disp,
                                             tipos=self.pieza("tipos_plural", c["event_type"])))
                    else:
                        lineas.append(self.f("tarjeta_aforo", n=aforo, disposicion=disp))
                    for a in res.get("avisos_zona", []):
                        lineas.append(self.f("aviso_zona", hasta_general=e["chatbot_guardrails"]["max_end_time"],
                                             zona=self.pieza("zonas", a["zona"]), hasta=a["hasta"]))
                    t = self._tarjeta(c["espacio"], lineas, res.get("foto"), botones=False)
                    ui = self.ui()
                    t["botones"] = [{"texto": ui["ver_plano"], "accion": f"plano:{c['espacio']}"},
                                    {"texto": ui["ver_fotos"], "accion": f"fotos:{c['espacio']}"}]
                    r.bloque({"tipo": "tarjetas", "tarjetas": [t]})
                if res.get("grupo") == "bajo_60" and res.get("opcion_comodo"):
                    o = res["opcion_comodo"]
                    r.texto(self.f("elegido_amplio", espacio=self.nombre(o["id"]),
                                   n=str(self.espacios[o["id"]]["capacities"][c["disposicion"]])))
            elif self._dias() is not None:
                r.texto(self.f("revalidacion_ok", espacio=self.nombre(c["espacio"])))
            self.validado = (c["espacio"], c["fecha"], c["hora_fin"])
            return
        # No encaja: motivo con el dato del script y alternativas del script (router §3)
        aforo = None
        for m in res["motivos"]:
            if m["motivo"] == "antelacion":
                r.texto(self.f("descarte_antelacion", espacio=self.nombre(c["espacio"]), dias=str(m["necesita_dias"])))
            elif m["motivo"] == "horario":
                r.texto(self._descarte({"id": c["espacio"], "motivo": "horario"}))
            else:
                aforo = m
        if aforo:   # por aforo, se pregunta antes de enseñar otras opciones
            r.pregunta_ya(self.f("descarte_aforo", espacio=self.nombre(c["espacio"]), n=str(aforo["asistentes"]),
                                 disposicion=self.pieza("disposiciones", aforo["disposicion"]), aforo=str(aforo["aforo"])))
            self._alternativas = res.get("alternativas", [])
            c["espacio"], self.validado = None, None
            self.fase = "oferta_alternativas"
            return
        c["espacio"], self.validado = None, None
        self._mostrar_alternativas(res.get("alternativas", []), r)

    def _mostrar_alternativas(self, alternativas, r):
        if alternativas:
            self.recomendados = [x["id"] for x in alternativas]
            self.recomendado = True
            r.texto(self.f("intro_tarjetas"))
            self._tarjetas(alternativas, alternativas, r)
            r.pregunta(self.f("pregunta_final"))
        else:
            self._recomendar(r)

    # --- Información y media -----------------------------------------------------------
    def _info(self, tema, d, r):
        eid = d.get("espacio") or self.c["espacio"] or (self.recomendados[0] if len(self.recomendados) == 1 else None)
        r.otro_tema = True
        dato = None
        if eid:
            e = self.espacios[eid]
            g = e["chatbot_guardrails"]
            if tema == "parking":
                dato = g.get("parking")
            elif tema == "catering":
                dato = g.get("catering_policy")
            elif tema == "horario":
                dato = g.get("noise_curfew")
            elif tema == "accesibilidad":
                dato = next((a for a in e.get("amenities_included", []) if re.search(r"barreras|accesib", a, re.I)), None)
            elif tema == "equipamiento":
                encontrados = [a for a in e.get("amenities_included", [])
                               if re.search(r"wifi|proyector|pantalla|micr", a, re.I)]
                dato = ", ".join(encontrados) if encontrados else None
        if dato:
            dato = dato.strip().rstrip(".")
            r.texto(self.f("politica", espacio=self.nombre(eid), dato=dato[:1].lower() + dato[1:]))
            return
        if self.consulta_activa:
            r.texto(self.f("sin_dato_dentro"))
            donde = f" en {self.espacios[eid]['name']}" if eid else ""
            self._escalado(f"Pregunta por {tema}{donde}")
        else:
            r.texto(self.f("sin_dato_fuera"))
        self._decidir("pendiente_confirmar", "sin_dato")

    def _media(self, tipo, d, r):
        eid = d.get("espacio") or self.c["espacio"] or (self.recomendados[0] if len(self.recomendados) == 1 else None)
        if not eid:
            return
        r.otro_tema = True
        if tipo == "video":
            r.pregunta(self.f("video"))
            self.fase, self.fotos_de = "oferta_fotos", eid
        elif tipo == "plano":
            self._plano(eid, r)
        else:
            self._galeria(eid, r)

    def _plano(self, eid, r):
        planos = media_aprobada(eid, "plano")
        if planos:
            nombre = self.espacios[eid]["name"]
            sufijo = ".en" if self.idioma == "en" else ""   # etiquetas del plano en el idioma de la conversación
            r.bloque({"tipo": "plano", "url": f"/media/{planos[0]['id']}{sufijo}",
                      "alt": self.ui()["alt_plano"].format(nombre=nombre)})

    def _galeria(self, eid, r):
        nombre = self.espacios[eid]["name"]
        fotos = [{"url": f"/media/{m['id']}", "alt": self.ui()["alt_foto"].format(nombre=nombre), "pie": self.f("pie_foto")}
                 for m in media_aprobada(eid, "foto")]
        r.bloque({"tipo": "galeria", "titulo": self.f("galeria_titulo", nombre=nombre), "fotos": fotos})

    # --- Envío, registro y cierre ------------------------------------------------------
    def _datos_envio(self, conversacion_extra=(), sin_envio=False):
        c = self.c
        enr = self._router(consulta_en_marcha=self.consulta_activa)
        decision = enr["decision"] or self.decision or "ninguna"
        motivo = enr["motivo_escalado"] if enr["decision"] else self.motivo
        turnos = self.historial + list(conversacion_extra)
        return {
            "id_conversacion": self.id, "idioma": self.idioma,
            "ruta": enr["ruta"], "rutas_adicionales": enr["rutas_adicionales"],
            "decision": decision, "motivo_escalado": motivo, "accion": enr["accion"],
            "consulta": {"tipo_evento": c["tipo"] or "", "asistentes": c["asistentes_texto"] or "",
                         "espacio_elegido": self.espacios[c["espacio"]]["name"] if c["espacio"] else "",
                         "zona": c["zona"] or "", "fecha": c["fecha"] if c["fecha_nivel"] == "dia" else "",
                         "presupuesto": c["presupuesto"] or "", "necesidades": c["necesidades"] or "",
                         "escalados": list(self.escalados)},
            "cliente": dict(self.cliente),
            "privacidad": "sin_respuesta" if sin_envio else self.privacidad,
            "publicidad": self.publicidad,
            "conversacion": [{"quien": q, "texto": t} for q, t in turnos],
        }

    def _enviar(self, r):
        extra = [("bot", " ".join(m["texto"] for m in r.mensajes if m["tipo"] == "texto"))] if r.mensajes else []
        res = procesar(self._datos_envio(extra), url=self.url, clave=self.clave, registro=self.registro)
        self.resultado_envio = res
        self.registrada = True
        self.fase = "enviado"
        if res.get("frase"):
            r.texto(res["frase"])

    def _cerrar(self, r, sin_envio=False, despedida=True):
        if not self.registrada:
            if self.fase == "publicidad" and not sin_envio:
                self.publicidad = "no"
                self._enviar(r)
            else:
                procesar(self._datos_envio(sin_envio=sin_envio), url=self.url, clave=self.clave, registro=self.registro)
                self.registrada = True
        if despedida:
            r.texto(self.f("despedida"))
        self.cerrada = True
        return self._salida(r)

    def cerrar_por_inactividad(self):
        if not self.cerrada:
            self._cerrar(Respuesta(), despedida=False)

    # --- Salida ------------------------------------------------------------------------
    def _salida(self, r, sin_repetir=False):
        # Volver a la privacidad pendiente una sola vez (consentimiento §4)
        if not sin_repetir and getattr(self, "_repetir_privacidad", False) and self.fase == "privacidad" and self.priv_veces < 2 \
                and not any(p["privacidad"] for p in r.cola):
            self._preguntar_privacidad(r, prefijo=self.f("volviendo") + " ")
        self._repetir_privacidad = False
        # Una sola pregunta de sí/no a la vez: si queda pendiente la oferta de fotos, la privacidad
        # espera al turno siguiente (si no, el "sí" del cliente no sabría a qué responde)
        if self.fase == "oferta_fotos":
            r.cola = [p for p in r.cola if not p["privacidad"]]
        # Preguntas en cola: como mucho dos por mensaje
        emitidas = []
        for p in r.cola:
            if r.n_preguntas + p["n"] > 2:
                continue
            texto = p["texto"]
            repetida = any(k in self.preguntados for k in p["claves"])
            if not emitidas and p["claves"] and (r.otro_tema or repetida):
                texto = self.f("volviendo") + " " + texto
            r.texto(texto)
            r.n_preguntas += p["n"]
            emitidas.append(p)
            for k in p["claves"]:
                self.preguntados.append(k)
                r.preguntadas.append(k)
            if p["botones"]:
                r.botones = p["botones"]
            if p["privacidad"]:
                self.fase = "privacidad"
                self.priv_veces += 1
                r.pregunto_privacidad = True
        if r.preguntadas or emitidas:
            self.ultimas = list(r.preguntadas)
        texto_bot = " ".join(self._texto_plano(m) for m in r.mensajes).strip()
        if texto_bot:
            self.historial.append(("bot", texto_bot))
        ui = self.ui()
        return {"idioma": self.idioma, "ui": ui, "mensajes": r.mensajes, "botones": r.botones,
                "formulario": r.formulario, "cerrada": self.cerrada}

    @staticmethod
    def _texto_plano(m):
        if m["tipo"] == "texto":
            return m["texto"]
        if m["tipo"] == "tarjetas":
            return " ".join(f"{t['nombre']}. " + " ".join(t["lineas"]) for t in m["tarjetas"])
        if m["tipo"] == "galeria":
            return m["titulo"]
        if m["tipo"] == "plano":
            return m["alt"]
        return ""
