/**
 * Explicaciones didácticas de cada paso de la simulación.
 * Traducción de core/explicaciones.py (misma redacción, carácter por carácter).
 *
 * Este módulo NO ejecuta ni duplica el algoritmo: solo lee los snapshots que ya produjo el
 * motor y el grafo (para conocer el peso de cada arista). Devuelve bloques de texto con un
 * estilo semántico que la pantalla se encarga de dibujar.
 */

import { ACTUALIZACION, FINAL, INFINITO, INICIO, SELECCION, formatoDistancia } from "./engine.js";

// Estilos de los bloques
export const TITULO = "titulo"; // encabezado de sección
export const TEXTO = "texto"; // párrafo
export const CALCULO = "calculo"; // línea de cálculo (tipografía monoespaciada)
export const TABLA = "tabla"; // fila de una tabla de texto (monoespaciada)
export const NOTA = "nota"; // aclaración secundaria
export const EXITO = "exito"; // resultado favorable
export const ALERTA = "alerta"; // resultado desfavorable

export function Bloque(estilo, texto) {
  return Object.freeze({ estilo, texto });
}

/** `breve` es lo que se ve en el panel; `detalle` alimenta «Más detalles». */
export function Explicacion(titulo, subtitulo, breve, detalle) {
  return Object.freeze({ titulo, subtitulo, breve: Object.freeze([...breve]), detalle: Object.freeze([...detalle]) });
}

Explicacion.textoPlano = (bloques) => bloques.map((b) => b.texto).join("\n");

// ---------------------------------------------------------------------- utilidades

const _d = formatoDistancia;

function _lista(vertices) {
  const v = [...vertices];
  if (v.length === 0) return "ninguno";
  if (v.length === 1) return v[0];
  return v.slice(0, -1).join(", ") + " y " + v[v.length - 1];
}

function _formula(distanciaU, peso, nueva, u, v) {
  return `${u} → ${v}: ${_d(distanciaU)} + ${peso} = ${_d(nueva)}`;
}

function _etiquetaDescartada(snapshot, v) {
  const par = snapshot.etiquetasDescartadas.find(([vert]) => vert === v);
  return par ? par[1] : null;
}

function _bloqueEtiquetas() {
  return [
    Bloque(TITULO, "Cómo leer una etiqueta [d, V]ₙ"),
    Bloque(
      TEXTO,
      "d es la distancia acumulada desde el origen; V es el predecesor, es decir, " +
        "el vértice por el que se llega con esa distancia; el subíndice n indica en " +
        "qué iteración se asignó la etiqueta. Si dos recorridos empatan en distancia, " +
        "el vértice conserva una etiqueta por cada predecesor.",
    ),
  ];
}

function _tablaEstado(snapshot, grafo) {
  const filas = [
    Bloque(TITULO, "Estado de todos los vértices"),
    Bloque(TABLA, `${"Vértice".padEnd(8)}${"Distancia".padEnd(11)}${"Predecesor".padEnd(13)}Estado`),
  ];
  for (const v of grafo.vertices) {
    const distancia = snapshot.distancias[v];
    const preds = (snapshot.predecesores[v] ?? []).join("/") || "-";
    let estado;
    if (snapshot.visitados.has(v)) estado = "visitado";
    else if (distancia === INFINITO) estado = "sin alcanzar";
    else estado = "pendiente";
    filas.push(Bloque(TABLA, `${v.padEnd(8)}${_d(distancia).padEnd(11)}${preds.padEnd(13)}${estado}`));
  }
  return filas;
}

function _anterior(resultado, indice) {
  return indice > 0 ? resultado.snapshots[indice - 1] : null;
}

/** Orden de Python para `sorted(key=(distancia, vértice))`. */
function porDistanciaYNombre(distancias) {
  return (a, b) => distancias[a] - distancias[b] || (a < b ? -1 : a > b ? 1 : 0);
}

// ------------------------------------------------------------------------- API

/** Explicación del snapshot `indice` a partir del estado ya calculado. */
export function explicar(grafo, resultado, indice) {
  const snapshot = resultado.snapshots[indice];
  if (snapshot.subpaso === INICIO) return _explicarInicio(grafo, resultado, snapshot);
  if (snapshot.subpaso === SELECCION) return _explicarSeleccion(grafo, resultado, indice, snapshot);
  if (snapshot.subpaso === ACTUALIZACION) return _explicarActualizacion(grafo, resultado, indice, snapshot);
  return _explicarFinal(grafo, resultado, snapshot);
}

// ---------------------------------------------------------------------- inicio

function _explicarInicio(grafo, resultado, snapshot) {
  const o = resultado.origen;
  if (o === resultado.destino) {
    const breve = [
      Bloque(TITULO, "Qué hace"),
      Bloque(
        TEXTO,
        `Etiqueta el origen ${o} con [0, -]₀. Como el destino es el mismo vértice, ya no hay nada más que calcular.`,
      ),
      Bloque(TITULO, "Origen y destino coinciden"),
      Bloque(
        TEXTO,
        `La distancia de un vértice a sí mismo es 0, así que Dijkstra termina de inmediato: el camino mínimo es solo ${o}.`,
      ),
    ];
    const detalle = [
      ...breve,
      Bloque(
        TEXTO,
        "No se genera ninguna iteración de selección ni de actualización: " +
          "no se elige ningún otro vértice ni se examina ninguna arista.",
      ),
      Bloque(TEXTO, "Para ver el algoritmo en acción, elige un destino distinto del origen."),
      ..._bloqueEtiquetas(),
      ..._tablaEstado(snapshot, grafo),
    ];
    return Explicacion(snapshot.titulo, "Etiquetado inicial", breve, detalle);
  }
  const breve = [
    Bloque(TITULO, "Qué hace"),
    Bloque(
      TEXTO,
      `Prepara el algoritmo: etiqueta el origen ${o} con [0, -]₀ y deja ` +
        "todos los demás vértices a distancia infinita (∞).",
    ),
    Bloque(TITULO, "Por qué"),
    Bloque(
      TEXTO,
      `Se parte de ${o} porque la distancia de un vértice a sí mismo es 0; ` +
        "de ahí en adelante, cada distancia se construye a partir de otra ya conocida.",
    ),
  ];
  const detalle = [
    Bloque(TITULO, "Qué ocurre en este paso"),
    Bloque(
      TEXTO,
      "Antes de procesar nada, el algoritmo registra lo único que se sabe con certeza: " +
        `llegar a ${o} desde ${o} cuesta 0. Para el resto de vértices todavía no se conoce ` +
        "ningún recorrido, así que su distancia acumulada es infinita (∞) y no tienen predecesor.",
    ),
    Bloque(TITULO, "Qué vendrá después"),
    Bloque(TEXTO, "Dijkstra repite dos subpasos hasta quedarse sin vértices alcanzables:"),
    Bloque(TEXTO, "1. Selección: se elige, entre los vértices aún no visitados, el de menor distancia acumulada."),
    Bloque(
      TEXTO,
      "2. Actualización: se examinan las aristas que salen del vértice elegido y, para cada " +
        "vecino no visitado, se compara la distancia que ofrece pasar por él con la etiqueta que " +
        "el vecino ya tenía.",
    ),
    ..._bloqueEtiquetas(),
    ..._tablaEstado(snapshot, grafo),
  ];
  return Explicacion(snapshot.titulo, "Etiquetado inicial", breve, detalle);
}

// ------------------------------------------------------------------- selección

function _explicarSeleccion(grafo, resultado, indice, snapshot) {
  const previo = _anterior(resultado, indice);
  const u = snapshot.seleccionado;
  const dU = snapshot.distancias[u];
  const candidatos = grafo.vertices
    .filter((v) => !previo.visitados.has(v) && previo.distancias[v] !== INFINITO)
    .sort(porDistanciaYNombre(previo.distancias));
  const empatados = candidatos.filter((v) => v !== u && previo.distancias[v] === dU);
  const otros = candidatos.filter((v) => v !== u);
  const sinAlcanzar = grafo.vertices.filter((v) => !previo.visitados.has(v) && previo.distancias[v] === INFINITO);
  const listaCandidatos = candidatos.map((v) => `${v} (${_d(previo.distancias[v])})`).join(", ");

  let porQue;
  if (dU === 0) {
    porQue =
      "El origen tiene distancia 0, la menor posible (los pesos son positivos): " +
      "siempre es el primero en procesarse y su etiqueta ya es definitiva.";
  } else {
    porQue =
      "Con pesos positivos, ningún recorrido que pase por otros vértices pendientes puede llegar a " +
      `${u} con menos de ${_d(dU)}: por eso su etiqueta ya es definitiva.`;
  }
  if (empatados.length) {
    porQue +=
      ` ${_lista(empatados)} tiene${empatados.length > 1 ? "n" : ""} la misma distancia; ` +
      "el empate se resuelve por orden alfabético y no se pierde ningún camino mínimo.";
  }

  let corto =
    dU !== 0
      ? `Con pesos positivos, ningún otro recorrido puede llegar a ${u} con menos de ${_d(dU)}: ` +
        "su etiqueta ya es definitiva."
      : "El origen tiene distancia 0, la menor posible: siempre se procesa primero.";
  if (empatados.length) corto += ` Empata con ${_lista(empatados)}: se desempata por orden alfabético.`;
  const breve = [
    Bloque(TITULO, "Qué hace"),
    Bloque(TEXTO, `Elige ${u}, el vértice no visitado con menor distancia acumulada (${_d(dU)}).`),
    Bloque(TITULO, "Candidatos"),
    Bloque(CALCULO, listaCandidatos),
    Bloque(TITULO, "Por qué"),
    Bloque(TEXTO, corto),
  ];
  if (u === resultado.destino && u !== resultado.origen) {
    breve.push(
      Bloque(
        NOTA,
        `${u} es el destino, pero se sigue con los demás vértices alcanzables ` +
          "para no perder predecesores de igual distancia.",
      ),
    );
  }

  const detalle = [
    Bloque(TITULO, "Qué ocurre en este paso"),
    Bloque(
      TEXTO,
      `Subpaso 1 de la iteración ${snapshot.iteracion}: selección. El algoritmo mira todos los ` +
        "vértices que todavía no se han visitado y que ya tienen una distancia finita, y elige el menor.",
    ),
    Bloque(TITULO, "Vértices candidatos (no visitados con distancia finita)"),
    ...candidatos.map((v) =>
      Bloque(
        CALCULO,
        `${v.padEnd(3)} distancia ${_d(previo.distancias[v]).padEnd(4)} etiqueta ${previo.etiqueta(v)}` +
          (v === u ? "   ← elegido" : ""),
      ),
    ),
  ];
  if (sinAlcanzar.length) {
    detalle.push(Bloque(NOTA, `Todavía sin alcanzar (distancia ∞), por lo que no compiten: ${_lista(sinAlcanzar)}.`));
  }
  detalle.push(
    Bloque(TITULO, "Por qué es correcto elegir " + u),
    Bloque(TEXTO, porQue),
    Bloque(
      TEXTO,
      "Cualquier otro recorrido hacia " +
        u +
        " tendría que pasar antes por un vértice pendiente, " +
        "cuya distancia ya es igual o mayor, y sumarle pesos positivos solo puede aumentar el total.",
    ),
  );
  if (otros.length === 0) detalle.push(Bloque(NOTA, `${u} es el único candidato en este momento.`));
  detalle.push(
    Bloque(TITULO, "Qué vendrá después"),
    Bloque(TEXTO, `${u} pasa a la lista de visitados. En el subpaso siguiente se examinarán sus aristas salientes.`),
    ..._bloqueEtiquetas(),
    ..._tablaEstado(snapshot, grafo),
  );
  return Explicacion(snapshot.titulo, "Subpaso 1 · Selección", breve, detalle);
}

// ----------------------------------------------------------------- actualización

/** [fórmula, conclusión corta, conclusión larga] de una arista evaluada. */
function _lineasDeArista(grafo, snapshot, anterior, u, v, tipo) {
  const dU = snapshot.distancias[u];
  const peso = grafo.peso(u, v);
  const nueva = dU + peso;
  const antes = anterior.distancias[v];
  const formula = _formula(dU, peso, nueva, u, v);
  let corta;
  let larga;
  if (tipo === "mejora" && antes === INFINITO) {
    corta = `${v} no tenía distancia (∞): se etiqueta ${v} con ${snapshot.etiqueta(v)}.`;
    larga =
      `${v} todavía no había sido alcanzado (distancia ∞), así que cualquier recorrido es mejor: ` +
      `se le asigna la etiqueta ${snapshot.etiqueta(v)}, con ${u} como predecesor.`;
  } else if (tipo === "mejora") {
    const vieja = _etiquetaDescartada(snapshot, v) || anterior.etiqueta(v);
    corta = `${_d(nueva)} < ${_d(antes)}: se reemplaza ${vieja} por ${snapshot.etiqueta(v)}.`;
    larga =
      `${_d(nueva)} es menor que la distancia actual de ${v} (${_d(antes)}): pasar por ${u} es un ` +
      `recorrido más corto. La etiqueta anterior ${vieja} se descarta (aparece tachada) y ${v} ` +
      `pasa a tener ${snapshot.etiqueta(v)}.`;
  } else if (tipo === "empate") {
    corta = `${_d(nueva)} = ${_d(antes)}: empate, ${v} conserva su distancia y suma a ${u} como predecesor.`;
    larga =
      `${_d(nueva)} es igual a la distancia actual de ${v} (${_d(antes)}). No hay un recorrido mejor, ` +
      `pero sí otro igual de corto: ${v} conserva su distancia y registra también a ${u} como ` +
      `predecesor (${snapshot.etiqueta(v)}). Así se conservan todos los caminos mínimos.`;
  } else {
    corta = `${_d(nueva)} > ${_d(antes)}: se conserva la etiqueta actual de ${v}.`;
    larga =
      `${_d(nueva)} es mayor que la distancia actual de ${v} (${_d(antes)}): pasar por ${u} no mejora ` +
      `nada, así que ${v} conserva su etiqueta ${anterior.etiqueta(v)}. El cálculo queda tachado ` +
      "en la tabla.";
  }
  return [formula, corta, larga];
}

function _explicarActualizacion(grafo, resultado, indice, snapshot) {
  const anterior = _anterior(resultado, indice); // snapshot de la selección: estado ANTES de actualizar
  const u = snapshot.seleccionado;
  const dU = snapshot.distancias[u];
  const evaluadas = [...snapshot.aristasEvaluadas];
  const omitidas = grafo.salientes(u).map(([w]) => w).filter((w) => snapshot.visitados.has(w));

  const porQue =
    `Pasar por ${u} puede acortar el camino a sus vecinos. Cada vecino conserva la menor ` +
    "distancia (y todos los predecesores si hay empate).";

  const breve = [
    Bloque(TITULO, "Qué hace"),
    Bloque(
      TEXTO,
      `Examina las aristas de ${u} (distancia ${_d(dU)}) hacia vértices no visitados: distancia(${u}) + peso.`,
    ),
  ];
  if (evaluadas.length) {
    breve.push(Bloque(TITULO, "Cálculos"));
    for (const [, v, tipo] of evaluadas) {
      const [formula, corta] = _lineasDeArista(grafo, snapshot, anterior, u, v, tipo);
      breve.push(Bloque(CALCULO, formula));
      breve.push(Bloque(TEXTO, "   " + corta));
    }
  } else {
    breve.push(Bloque(TEXTO, `${u} no tiene aristas hacia vértices no visitados: no hay etiquetas que actualizar.`));
  }
  if (omitidas.length) {
    breve.push(
      Bloque(
        NOTA,
        `Se omiten las aristas hacia ${_lista(omitidas)}: ya están visitados y su distancia es definitiva.`,
      ),
    );
  }
  breve.push(Bloque(TITULO, "Por qué"), Bloque(TEXTO, porQue));

  const detalle = [
    Bloque(TITULO, "Qué ocurre en este paso"),
    Bloque(
      TEXTO,
      `Subpaso 2 de la iteración ${snapshot.iteracion}: actualización. ${u} ya está visitado ` +
        `con distancia ${_d(dU)}. Para cada arista ${u} → v hacia un vértice no visitado se calcula ` +
        `distancia nueva = d(${u}) + peso(${u}, v) y se compara con la distancia actual de v.`,
    ),
    Bloque(TITULO, "Reglas de comparación"),
    Bloque(TEXTO, "• Si la distancia nueva es menor: se reemplaza la etiqueta (la anterior se descarta)."),
    Bloque(TEXTO, "• Si es igual: se conserva la distancia y se añade un predecesor (hay otro camino igual de corto)."),
    Bloque(TEXTO, "• Si es mayor: no se cambia nada."),
  ];
  if (evaluadas.length) {
    detalle.push(Bloque(TITULO, "Cálculo arista por arista"));
    for (const [, v, tipo] of evaluadas) {
      const [formula, , larga] = _lineasDeArista(grafo, snapshot, anterior, u, v, tipo);
      detalle.push(Bloque(CALCULO, formula));
      detalle.push(Bloque(TEXTO, larga));
    }
  } else {
    detalle.push(
      Bloque(
        TEXTO,
        `${u} no tiene aristas salientes hacia vértices no visitados; el paso no modifica ninguna etiqueta.`,
      ),
    );
  }
  if (omitidas.length) {
    detalle.push(
      Bloque(
        NOTA,
        `Aristas omitidas: ${u} → ${_lista(omitidas)}. Esos vértices ya fueron visitados, ` +
          "lo que significa que su distancia mínima ya es definitiva y no puede mejorarse.",
      ),
    );
  }
  const siguiente = indice + 1 < resultado.snapshots.length ? resultado.snapshots[indice + 1] : null;
  detalle.push(Bloque(TITULO, "Qué vendrá después"));
  if (siguiente !== null && siguiente.subpaso === FINAL) {
    detalle.push(
      Bloque(TEXTO, "No quedan vértices alcanzables sin visitar: el siguiente paso muestra el resultado final."),
    );
  } else {
    detalle.push(
      Bloque(
        TEXTO,
        "Se volverá a elegir, entre los no visitados con distancia finita, el de menor distancia acumulada.",
      ),
    );
  }
  detalle.push(..._bloqueEtiquetas(), ..._tablaEstado(snapshot, grafo));
  return Explicacion(snapshot.titulo, "Subpaso 2 · Actualización", breve, detalle);
}

// -------------------------------------------------------------------------- final

function _explicarFinal(grafo, resultado, snapshot) {
  const o = resultado.origen;
  const d = resultado.destino;
  const alcanzados = grafo.vertices.filter((v) => snapshot.distancias[v] !== INFINITO);
  // El cuadro «Resultado» de la pantalla ya muestra distancia y caminos: aquí se explica qué significan.
  const porQueFin =
    "Terminó porque no queda ningún vértice no visitado con distancia finita: " +
    "las distancias de todos los alcanzables ya son definitivas.";

  if (o === d) {
    const breve = [
      Bloque(TITULO, "Origen y destino coinciden"),
      Bloque(
        TEXTO,
        `${o} es a la vez origen y destino: la distancia mínima es 0 y el camino mínimo es solo el vértice ${o}.`,
      ),
      Bloque(
        TEXTO,
        "Dijkstra terminó de inmediato: no hubo selecciones ni actualizaciones, " +
          "y no se recorrió ninguna arista.",
      ),
    ];
    const detalle = [...breve, ..._bloqueEtiquetas(), ..._tablaEstado(snapshot, grafo)];
    return Explicacion(snapshot.titulo, "Fin de la simulación", breve, detalle);
  }

  if (!resultado.alcanzable) {
    const breve = [
      Bloque(TITULO, "Qué hace"),
      Bloque(TEXTO, porQueFin),
      Bloque(TITULO, "Por qué no hay camino"),
      Bloque(ALERTA, `${d} nunca recibió una etiqueta (distancia ∞).`),
      Bloque(TEXTO, `Desde ${o} solo se pueden alcanzar ${_lista(alcanzados)}.`),
    ];
    const detalle = [...breve, ..._bloqueEtiquetas(), ..._tablaEstado(snapshot, grafo)];
    return Explicacion(snapshot.titulo, "Fin de la simulación", breve, detalle);
  }

  const n = resultado.cantidadCaminos;
  const lineasCaminos = resultado.caminos.map((camino) => {
    const pesos = [];
    for (let i = 0; i + 1 < camino.length; i++) pesos.push(grafo.peso(camino[i], camino[i + 1]));
    const suma = pesos.reduce((a, b) => a + b, 0);
    return Bloque(CALCULO, camino.join(" → ") + "   =   " + pesos.join(" + ") + ` = ${_d(suma)}`);
  });
  const plural = n !== 1;
  const breve = [
    Bloque(TITULO, "Qué hace"),
    Bloque(TEXTO, porQueFin),
    Bloque(TITULO, "Cómo se obtuvo"),
    Bloque(
      TEXTO,
      `La etiqueta de ${d} es ${snapshot.etiqueta(d)}. Siguiendo los predecesores hacia atrás, ` +
        `desde ${d} hasta ${o}, se reconstruye ` +
        (plural ? "cada camino mínimo." : "el camino mínimo."),
    ),
  ];
  if (resultado.truncado) breve.push(Bloque(NOTA, "Se muestra solo una parte de los caminos por su elevada cantidad."));
  const detalle = [
    Bloque(EXITO, `Distancia mínima de ${o} a ${d}: ${_d(resultado.distancia)}.`),
    Bloque(TITULO, "Cómo se obtuvo"),
    Bloque(
      TEXTO,
      `La etiqueta de ${d} es ${snapshot.etiqueta(d)}. Para reconstruir el recorrido se sigue ` +
        `hacia atrás el predecesor de cada vértice, desde ${d} hasta ${o}.`,
    ),
    Bloque(
      TEXTO,
      plural
        ? `Existen ${n} caminos mínimos distintos porque al menos un vértice del recorrido ` +
            "conservó varios predecesores con la misma distancia."
        : "Cada vértice del recorrido tiene un único predecesor, así que el camino mínimo es único.",
    ),
    Bloque(TITULO, "Caminos mínimos y suma de pesos"),
    ...lineasCaminos,
    Bloque(TEXTO, porQueFin),
    ..._bloqueEtiquetas(),
    ..._tablaEstado(snapshot, grafo),
  ];
  return Explicacion(snapshot.titulo, "Fin de la simulación", breve, detalle);
}
