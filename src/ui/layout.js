/**
 * Disposición del grafo y colocación de textos sin solapes. Módulo puro (sin DOM):
 * se prueba con Node y lo usa el componente SVG.
 *
 * Sistema de coordenadas virtual: ANCHO × ALTO (el SVG lo escala con viewBox).
 *  - posicionesPorCapas: capas de izquierda a derecha, reduciendo cruces (mediana/baricentro).
 *  - geometriaAristas: cada arista es una curva de Bézier cuadrática que esquiva los vértices.
 *  - colocarRotulos: pesos, marcas ORIGEN/DESTINO y etiquetas de Dijkstra, eligiendo para cada
 *    uno el hueco con menos colisiones entre una lista de candidatos.
 */

export const ANCHO = 1000;
export const ALTO = 600;
export const RADIO = 22;
export const MARGEN = 46;
export const ANCHO_CARACTER = 8.6; // estimación por exceso de un carácter monoespaciado de 13 px
export const ALTO_LINEA = 17;

/* --------------------------------------------------------------------- capas */

/** Capa de cada vértice: longitud del camino más largo desde una fuente (el grafo es un DAG). */
export function calcularCapas(grafo) {
  const capas = {};
  for (const v of grafo.vertices) capas[v] = 0;
  let orden;
  try {
    orden = grafo.ordenTopologico();
  } catch {
    orden = grafo.vertices;
  }
  for (const u of orden) {
    for (const [w] of grafo.salientes(u)) capas[w] = Math.max(capas[w], capas[u] + 1);
  }
  return capas;
}

function mediana(valores) {
  if (!valores.length) return null;
  const s = [...valores].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function contarCruces(aristas, capas, indice) {
  let cruces = 0;
  for (let i = 0; i < aristas.length; i++) {
    const [a, b] = aristas[i];
    for (let j = i + 1; j < aristas.length; j++) {
      const [c, d] = aristas[j];
      if (capas[a] !== capas[c] || capas[b] !== capas[d]) continue;
      if ((indice[a] - indice[c]) * (indice[b] - indice[d]) < 0) cruces++;
    }
  }
  return cruces;
}

/** Orden vertical dentro de cada capa (varias pasadas de mediana de los vecinos, se queda con el mejor). */
export function ordenarPorCapas(grafo, capas) {
  const columnas = {};
  for (const v of grafo.vertices) (columnas[capas[v]] ??= []).push(v);
  const claves = Object.keys(columnas).map(Number).sort((a, b) => a - b);
  const aristas = grafo.aristas().map(([u, v]) => [u, v]);
  const indices = () => {
    const idx = {};
    for (const k of claves) columnas[k].forEach((v, i) => (idx[v] = i));
    return idx;
  };
  let mejor = null;
  let mejorCruces = Infinity;
  const guardar = () => {
    const c = contarCruces(aristas, capas, indices());
    if (c < mejorCruces) {
      mejorCruces = c;
      mejor = Object.fromEntries(claves.map((k) => [k, [...columnas[k]]]));
    }
  };
  guardar();
  for (let pasada = 0; pasada < 8 && mejorCruces > 0; pasada++) {
    const haciaAdelante = pasada % 2 === 0;
    const secuencia = haciaAdelante ? claves.slice(1) : claves.slice(0, -1).reverse();
    for (const k of secuencia) {
      const idx = indices();
      const med = {};
      for (const v of columnas[k]) {
        const vecinos = haciaAdelante
          ? grafo.entrantes(v).map(([u]) => idx[u])
          : grafo.salientes(v).map(([w]) => idx[w]);
        med[v] = mediana(vecinos);
      }
      const posAct = {};
      columnas[k].forEach((v, i) => (posAct[v] = i));
      columnas[k] = [...columnas[k]].sort((a, b) => {
        const ma = med[a] ?? posAct[a];
        const mb = med[b] ?? posAct[b];
        return ma - mb || posAct[a] - posAct[b];
      });
    }
    guardar();
  }
  return Object.fromEntries(claves.map((k) => [k, mejor[k]]));
}

/** Posiciones `{v: [x, y]}` por capas, de izquierda a derecha, ocupando todo el área. */
export function posicionesPorCapas(grafo) {
  const capas = calcularCapas(grafo);
  const columnas = ordenarPorCapas(grafo, capas);
  const claves = Object.keys(columnas).map(Number).sort((a, b) => a - b);
  const pos = {};
  const nCapas = claves.length;
  const alto = ALTO - 2 * MARGEN;
  const ancho = ANCHO - 2 * MARGEN;
  claves.forEach((k, i) => {
    const x = nCapas === 1 ? ANCHO / 2 : MARGEN + (ancho * i) / (nCapas - 1);
    const lista = columnas[k];
    lista.forEach((v, j) => {
      // Un pequeño zigzag en capas muy llenas evita que los textos de vértices vecinos se rocen.
      const y = lista.length === 1 ? ALTO / 2 : MARGEN + (alto * j) / (lista.length - 1);
      pos[v] = [x, y];
    });
  });
  return pos;
}

export function posicionesCirculares(vertices) {
  const n = vertices.length;
  const cx = ANCHO / 2;
  const cy = ALTO / 2;
  const rx = ANCHO / 2 - MARGEN - 40;
  const ry = ALTO / 2 - MARGEN - 8;
  const pos = {};
  vertices.forEach((v, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / n;
    pos[v] = [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
  });
  return pos;
}

export function limitar([x, y]) {
  return [Math.min(ANCHO - MARGEN / 2, Math.max(MARGEN / 2, x)), Math.min(ALTO - MARGEN / 2, Math.max(MARGEN / 2, y))];
}

/* ------------------------------------------------------------------ geometría */

const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

function bezier(p0, c, p2, t) {
  const u = 1 - t;
  return [u * u * p0[0] + 2 * u * t * c[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p2[1]];
}

function distanciaPuntoSegmento(p, a, b) {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const l2 = dx * dx + dy * dy;
  const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2));
  return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
}

function segmentosSeCruzan(a, b, c, d) {
  const o = (p, q, r) => (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
  return o(a, b, c) * o(a, b, d) < 0 && o(c, d, a) * o(c, d, b) < 0;
}

function cruces(pa, pb) {
  let n = 0;
  for (let i = 0; i < pa.length - 1; i += 2) {
    for (let j = 0; j < pb.length - 1; j += 2) {
      if (segmentosSeCruzan(pa[i], pa[i + 1], pb[j], pb[j + 1])) n++;
    }
  }
  return n;
}

const clave = (u, v) => `${u}>${v}`;
export { clave as claveArista };

/**
 * Para cada arista: puntos muestreados de la curva ya recortada contra los vértices, y la
 * dirección de llegada (para dibujar la punta de flecha).
 */
export function geometriaAristas(grafo, pos) {
  const salida = new Map();
  const previas = [];
  const vertices = grafo.vertices.filter((v) => pos[v]);
  // Las aristas más largas se colocan primero: son las que más necesitan esquivar.
  const aristas = grafo
    .aristas()
    .filter(([u, v]) => pos[u] && pos[v])
    .sort((a, b) => dist(pos[b[0]], pos[b[1]]) - dist(pos[a[0]], pos[a[1]]));
  for (const [u, v, peso] of aristas) {
    const p0 = pos[u];
    const p2 = pos[v];
    const largo = dist(p0, p2) || 1;
    const nx = -(p2[1] - p0[1]) / largo;
    const ny = (p2[0] - p0[0]) / largo;
    const mx = (p0[0] + p2[0]) / 2;
    const my = (p0[1] + p2[1]) / 2;
    let mejor = null;
    for (const desvio of [0, 34, -34, 66, -66, 100, -100, 140, -140, 190, -190]) {
      // En una Bézier cuadrática la flecha máxima es la mitad del desplazamiento del control.
      const c = [mx + nx * desvio * 2, my + ny * desvio * 2];
      const puntos = [];
      for (let i = 0; i <= 28; i++) puntos.push(bezier(p0, c, p2, i / 28));
      let choques = 0;
      for (const w of vertices) {
        if (w === u || w === v) continue;
        let minimo = Infinity;
        for (let i = 0; i < puntos.length - 1; i++) minimo = Math.min(minimo, distanciaPuntoSegmento(pos[w], puntos[i], puntos[i + 1]));
        if (minimo < RADIO + 12) choques++;
      }
      const fuera = puntos.some(([x, y]) => x < 8 || y < 8 || x > ANCHO - 8 || y > ALTO - 8);
      let cr = 0;
      for (const otra of previas) cr += cruces(puntos, otra);
      const coste = choques * 1e5 + (fuera ? 5e3 : 0) + cr * 25 + Math.abs(desvio) * 0.8;
      if (!mejor || coste < mejor.coste) mejor = { coste, puntos, desvio };
      if (coste < 1) break; // línea recta sin choques ni cruces: no se busca más
    }
    previas.push(mejor.puntos);
    // Recorte contra los círculos de origen y destino
    let i0 = 0;
    while (i0 < mejor.puntos.length - 1 && dist(mejor.puntos[i0], p0) < RADIO + 1) i0++;
    let i1 = mejor.puntos.length - 1;
    while (i1 > i0 && dist(mejor.puntos[i1], p2) < RADIO + 3) i1--;
    const recortados = mejor.puntos.slice(i0, i1 + 1);
    const ultimo = recortados[recortados.length - 1];
    const previo = recortados[Math.max(0, recortados.length - 4)];
    const ang = Math.atan2(ultimo[1] - previo[1], ultimo[0] - previo[0]);
    salida.set(clave(u, v), { u, v, peso, puntos: recortados, completos: mejor.puntos, angulo: ang, desvio: mejor.desvio });
  }
  return salida;
}

/* ----------------------------------------------------------- rótulos sin solapes */

export function anchoTexto(texto, factor = ANCHO_CARACTER) {
  return Math.ceil([...String(texto)].length * factor) + 10;
}

const solapan = (a, b, pad = 2) =>
  a.x - a.w / 2 - pad < b.x + b.w / 2 && a.x + a.w / 2 + pad > b.x - b.w / 2 && a.y - a.h / 2 - pad < b.y + b.h / 2 && a.y + a.h / 2 + pad > b.y - b.h / 2;

function rectChocaCirculo(r, [cx, cy], radio) {
  const dx = Math.abs(cx - r.x) - r.w / 2;
  const dy = Math.abs(cy - r.y) - r.h / 2;
  const ex = Math.max(dx, 0);
  const ey = Math.max(dy, 0);
  return ex * ex + ey * ey < radio * radio;
}

function muestrasEnRect(r, puntos) {
  let n = 0;
  for (const [x, y] of puntos) if (Math.abs(x - r.x) < r.w / 2 + 2 && Math.abs(y - r.y) < r.h / 2 + 2) n++;
  return n;
}

/**
 * Coloca pesos, marcas y etiquetas. Devuelve `{pesos, marcas, etiquetas, choques}`:
 *  - `pesos`:    Map clave-arista → rectángulo {x,y,w,h} (centro) sobre la arista.
 *  - `marcas`:   Map vértice → rectángulo de la marca ORIGEN/DESTINO.
 *  - `etiquetas`:Map vértice → rectángulo reservado para [d, V]ₙ (y la etiqueta descartada).
 *  - `choques`:  cuántos rótulos no encontraron hueco libre (debería ser 0).
 *
 * @param {{pos, geometria, marcas?: Object<string,string>, etiquetas?: Object<string,{ancho:number, lineas:number}>}} p
 */
export function colocarRotulos({ pos, geometria, marcas = {}, etiquetas = {} }) {
  const vertices = Object.keys(pos);
  const ocupados = []; // rectángulos ya colocados
  const todasLasMuestras = [...geometria.values()].map((g) => g.completos);
  let choques = 0;

  const duro = (r, propia = null) => {
    let c = 0;
    if (r.x - r.w / 2 < 2 || r.x + r.w / 2 > ANCHO - 2 || r.y - r.h / 2 < 2 || r.y + r.h / 2 > ALTO - 2) c += 1;
    for (const v of vertices) if (rectChocaCirculo(r, pos[v], RADIO + 2)) c += 1;
    for (const o of ocupados) if (solapan(r, o)) c += 1;
    return c;
  };
  const blando = (r, propia) => {
    let c = 0;
    for (const [k, g] of geometria) {
      if (k === propia) continue;
      c += muestrasEnRect(r, g.completos);
    }
    return c;
  };

  const elegir = (candidatos, propia = null) => {
    let mejor = null;
    candidatos.forEach((r, i) => {
      const d = duro(r);
      const b = blando(r, propia); // las propias no cuentan
      const coste = d * 1e6 + b * 40 + i * 0.6;
      if (!mejor || coste < mejor.coste) mejor = { coste, r, d };
    });
    if (mejor.d > 0) choques++;
    ocupados.push(mejor.r);
    return mejor.r;
  };

  // 1. pesos: sobre la propia arista, en el punto con menos colisiones
  const pesos = new Map();
  const claves = [...geometria.keys()].sort();
  for (const k of claves) {
    const g = geometria.get(k);
    const w = anchoTexto(g.peso, 8.6);
    const cand = [];
    for (const t of [0.5, 0.42, 0.58, 0.34, 0.66, 0.27, 0.73, 0.2, 0.8, 0.14, 0.86]) {
      const [x, y] = g.completos[Math.round(t * (g.completos.length - 1))];
      cand.push({ x, y, w, h: 20 });
    }
    pesos.set(k, elegir(cand, k));
  }

  // 2. etiquetas de Dijkstra (primero las más grandes, que son las que menos opciones tienen)
  const etiquetasColocadas = new Map();
  const orden = vertices.filter((v) => etiquetas[v]).sort((a, b) => etiquetas[b].ancho * etiquetas[b].lineas - etiquetas[a].ancho * etiquetas[a].lineas || (a < b ? -1 : 1));
  for (const v of orden) {
    const { ancho, lineas } = etiquetas[v];
    const w = ancho;
    const h = ALTO_LINEA * lineas + 4;
    const [x, y] = pos[v];
    const cand = [];
    const direcciones = [-90, 90, -50, 50, -130, 130, 0, 180, -20, 20, -160, 160, -70, 70, -110, 110];
    const dentro = (r) => ({ ...r, x: Math.min(ANCHO - 3 - w / 2, Math.max(3 + w / 2, r.x)), y: Math.min(ALTO - 3 - h / 2, Math.max(3 + h / 2, r.y)) });
    for (const gap of [3, 12, 24, 40, 60]) {
      for (const grados of direcciones) {
        const a = (grados * Math.PI) / 180;
        const dx = Math.cos(a);
        const dy = Math.sin(a);
        const base = { x: x + dx * (RADIO + gap) + dx * (w / 2), y: y + dy * (RADIO + gap) + dy * (h / 2), w, h };
        cand.push(dentro(base));
        // Las etiquetas anchas se desplazan a lo largo del lado para esquivar a sus vecinas.
        const vertical = Math.abs(dy) > 0.9;
        for (const f of [-0.3, 0.3, -0.55, 0.55]) cand.push(dentro(vertical ? { ...base, x: base.x + f * w } : { ...base, y: base.y + f * h * 2 }));
      }
    }
    etiquetasColocadas.set(v, elegir(cand));
  }
  // 3. marcas (pequeñas y flexibles: se colocan al final, con lo que quede libre) ORIGEN / DESTINO
  const marcasColocadas = new Map();
  for (const v of vertices) {
    const texto = marcas[v];
    if (!texto) continue;
    const [x, y] = pos[v];
    const w = anchoTexto(texto, 7.4) + 6;
    const h = 18;
    const cand = [];
    for (const gap of [6, 20, 36]) for (const lado of [-1, 1]) for (const f of [0, -0.4, 0.4, -0.8, 0.8]) cand.push({ x: x + f * w, y: y + lado * (RADIO + gap + h / 2), w, h });
    for (const lado of [-1, 1]) for (const gap of [8, 24]) cand.push({ x: x + lado * (RADIO + gap + w / 2), y, w, h });
    marcasColocadas.set(v, elegir(cand));
  }

  return { pesos, marcas: marcasColocadas, etiquetas: etiquetasColocadas, choques };
}

/** Comprobación independiente (la usan las pruebas): lista de pares de elementos que se pisan. */
export function detectarSolapes({ pos, pesos, marcas, etiquetas }) {
  const problemas = [];
  const items = [];
  for (const [k, r] of pesos) items.push([`peso ${k}`, r]);
  for (const [v, r] of marcas) items.push([`marca ${v}`, r]);
  for (const [v, r] of etiquetas) items.push([`etiqueta ${v}`, r]);
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) if (solapan(items[i][1], items[j][1], 0)) problemas.push([items[i][0], items[j][0]]);
    for (const v of Object.keys(pos)) if (rectChocaCirculo(items[i][1], pos[v], RADIO)) problemas.push([items[i][0], `vértice ${v}`]);
  }
  return problemas;
}
