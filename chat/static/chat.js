// Chat web: solo pinta lo que devuelve el servidor. Nada de lógica de negocio aquí.
// Todo el texto se pone con textContent (nunca innerHTML) y las imágenes solo desde /media/.
"use strict";

const $ = (id) => document.getElementById(id);
const estado = { sesion: null, ui: {}, cerrada: false, idioma: "es" };

async function api(ruta, cuerpo) {
  const r = await fetch(ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) {
    const error = new Error(datos.error || estado.ui.error || "Error");
    error.sesionPerdida = Boolean(datos.sesion_perdida);
    error.limite = Boolean(datos.limite);   // 429: el servidor manda una frase amable para enseñar
    throw error;
  }
  return datos;
}

function el(etiqueta, clase, texto) {
  const n = document.createElement(etiqueta);
  if (clase) n.className = clase;
  if (texto !== undefined) n.textContent = texto;
  return n;
}

function bajar() {
  const m = $("mensajes");
  m.scrollTop = m.scrollHeight;
}

function burbuja(texto, quien) {
  $("mensajes").appendChild(el("p", "burbuja " + quien, texto));
  bajar();
}

function imagen(url, alt) {
  const img = el("img");
  if (typeof url === "string" && url.startsWith("/media/")) img.src = url;
  img.alt = alt || "";
  img.addEventListener("load", bajar);   // al cargar la imagen, el chat sigue abajo
  return img;
}

function aplicarUI(ui, idioma) {
  if (!ui) return;
  estado.ui = ui;
  estado.idioma = idioma || estado.idioma;
  document.documentElement.lang = idioma || "es";
  $("cabecera").textContent = ui.cabecera;
  document.title = ui.cabecera;
  $("terminar").textContent = ui.terminar;
  $("texto").placeholder = ui.campo;
  $("enviar").textContent = ui.enviar;
  $("pie").textContent = ui.pie;
  $("l-nombre").textContent = ui.f_nombre;
  $("l-email").textContent = ui.f_email;
  $("l-empresa").textContent = ui.f_empresa;
  $("l-telefono").textContent = ui.f_telefono;
  $("f-enviar").textContent = ui.f_enviar;
}

// enGrupo: los botones rápidos (privacidad, publicidad…) se desactivan juntos al pulsar uno;
// en las tarjetas solo se desactiva el pulsado ("Ver plano" no bloquea "Elegir este").
function botonesAccion(botones, contenedor, enGrupo) {
  for (const b of botones || []) {
    const boton = el("button", "boton", b.texto);
    boton.type = "button";
    boton.addEventListener("click", async () => {
      // Se desactiva mientras se envía, para no mandar dos veces lo mismo
      const desactivados = enGrupo ? [...contenedor.querySelectorAll("button")] : [boton];
      desactivados.forEach((x) => (x.disabled = true));
      const ok = await enviar({ accion: b.accion }, b.texto);
      if (!ok) desactivados.forEach((x) => (x.disabled = false));   // si falla, se puede volver a pulsar
    });
    contenedor.appendChild(boton);
  }
}

function pintarTarjetas(m) {
  const lista = el("div", "tarjetas");
  for (const t of m.tarjetas) {
    const tarjeta = el("article", "tarjeta");
    if (t.foto) {
      const fig = el("figure");
      fig.appendChild(imagen(t.foto.url, t.foto.alt));
      const pie = el("figcaption");
      (t.foto.pie || []).forEach((linea, i) => {
        if (i) pie.appendChild(el("br"));
        pie.appendChild(document.createTextNode(linea));
      });
      fig.appendChild(pie);
      tarjeta.appendChild(fig);
    }
    tarjeta.appendChild(el("h2", "", t.nombre));
    for (const linea of t.lineas) tarjeta.appendChild(el("p", "", linea));
    const acciones = el("div", "acciones");
    botonesAccion(t.botones, acciones, false);
    tarjeta.appendChild(acciones);
    lista.appendChild(tarjeta);
  }
  $("mensajes").appendChild(lista);
}

function pintarGaleria(m) {
  const g = el("section", "galeria");
  g.appendChild(el("h2", "", m.titulo));
  const rejilla = el("div", "rejilla");
  for (const f of m.fotos) {
    const fig = el("figure");
    fig.appendChild(imagen(f.url, f.alt));
    fig.appendChild(el("figcaption", "", f.pie));
    rejilla.appendChild(fig);
  }
  g.appendChild(rejilla);
  $("mensajes").appendChild(g);
}

function pintarPlano(m) {
  const fig = el("figure", "plano");
  fig.appendChild(imagen(m.url, m.alt));
  $("mensajes").appendChild(fig);
}

function pintar(res) {
  aplicarUI(res.ui, res.idioma);
  for (const m of res.mensajes || []) {
    if (m.tipo === "texto") burbuja(m.texto, "bot");
    else if (m.tipo === "tarjetas") pintarTarjetas(m);
    else if (m.tipo === "galeria") pintarGaleria(m);
    else if (m.tipo === "plano") pintarPlano(m);
  }
  if (res.botones && res.botones.length) {
    const zona = $("botones");
    zona.replaceChildren();
    botonesAccion(res.botones, zona, true);
  }
  $("formulario").hidden = !res.formulario;
  if (res.formulario) $("formulario").querySelector("input").focus();
  if (res.cerrada) cerrarUI();
  bajar();
}

function cerrarUI() {
  estado.cerrada = true;
  $("texto").disabled = true;
  $("enviar").disabled = true;
  $("terminar").disabled = true;
  $("botones").replaceChildren();
  $("formulario").hidden = true;
}

// La conversación ya no existe en el servidor (p. ej. se reinició): se empieza otra, en el mismo idioma
async function nuevaSesionTrasPerdida() {
  document.querySelectorAll("#mensajes button").forEach((x) => (x.disabled = true));   // botones de la anterior
  $("botones").replaceChildren();
  $("formulario").hidden = true;
  const r = await api("/api/nueva", { motivo: "sesion_perdida", idioma: estado.idioma });
  estado.sesion = r.sesion;
  pintar(r);
}

async function enviar(cuerpo, textoCliente) {
  if (estado.cerrada || !estado.sesion) return false;
  if (textoCliente) burbuja(textoCliente, "cliente");
  try {
    pintar(await api("/api/mensaje", { sesion: estado.sesion, ...cuerpo }));
    return true;
  } catch (e) {
    if (e.sesionPerdida) {
      try {
        await nuevaSesionTrasPerdida();
        return true;
      } catch (e2) { /* sigue abajo con el error genérico */ }
    }
    burbuja(e.limite ? e.message : (estado.ui.error || e.message), "bot error");
    return false;
  }
}

$("entrada").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const texto = $("texto").value.trim();
  if (!texto) return;
  $("texto").value = "";
  enviar({ texto }, texto);
});

$("formulario").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const datos = Object.fromEntries(new FormData($("formulario")).entries());
  const resumen = [datos.nombre, datos.email, datos.empresa, datos.telefono].filter(Boolean).join(" · ");
  $("formulario").hidden = true;
  $("botones").replaceChildren();
  enviar({ formulario: datos }, resumen);
});

$("terminar").addEventListener("click", async () => {
  if (estado.cerrada || !estado.sesion) return;
  try {
    pintar(await api("/api/cerrar", { sesion: estado.sesion }));
  } catch (e) {
    if (e.sesionPerdida) cerrarUI();   // ya no existe: no hay nada que cerrar
    else burbuja(estado.ui.error || e.message, "bot error");
  }
});

window.addEventListener("pagehide", () => {
  if (!estado.cerrada && estado.sesion) {
    navigator.sendBeacon("/api/cerrar", JSON.stringify({ sesion: estado.sesion }));
  }
});

(async () => {
  try {
    const r = await api("/api/nueva", {});
    estado.sesion = r.sesion;
    aplicarUI(r.ui, r.idioma);
    $("texto").focus();
  } catch (e) {
    burbuja(estado.ui.error || "Algo ha fallado por nuestra parte. Inténtalo de nuevo en un momento.", "bot error");
  }
})();
