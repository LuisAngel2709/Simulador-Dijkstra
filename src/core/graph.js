/**
 * Representación del grafo dirigido, ponderado y acíclico (DAG).
 * Traducción de core/graph.py. No depende de ninguna interfaz ni del navegador.
 */

export const NOMBRES_VERTICES = "ABCDEFGHIJKLMNOP"; // soporta hasta 16 vértices

export const PESO_MINIMO = 1;
export const PESO_MAXIMO = 99;

export const NODOS_MINIMO = 7;
export const NODOS_MAXIMO = 16;

/** Error de validación del grafo, con un mensaje apto para mostrar al usuario. */
export class GrafoError extends Error {
  constructor(mensaje) {
    super(mensaje);
    this.name = "GrafoError";
  }
}

// Formato estricto: solo dígitos ASCII 0-9 (con «-» opcional, únicamente para avisar de que
// los negativos no se admiten). Sin «+», guiones bajos, espacios internos ni otros alfabetos.
const ENTERO_ASCII = /^-?[0-9]+$/;
const ESPACIOS_EXTERIORES = " \t\r\n";
const MAX_DIGITOS = 9; // más dígitos que esto es, en cualquier caso, un valor fuera de rango

/** Equivalente de ``str.strip(chars)`` de Python. */
function quitarExteriores(texto, caracteres) {
  let i = 0;
  let j = texto.length;
  while (i < j && caracteres.includes(texto[i])) i++;
  while (j > i && caracteres.includes(texto[j - 1])) j--;
  return texto.slice(i, j);
}

/** Entero escrito en formato estricto, o ``null`` si el texto no tiene ese formato. */
function leerEntero(valor) {
  const texto = quitarExteriores(String(valor), ESPACIOS_EXTERIORES);
  if (!ENTERO_ASCII.test(texto)) return null;
  const negativo = texto.startsWith("-");
  const digitos = negativo ? texto.slice(1) : texto;
  if (digitos.length > MAX_DIGITOS) return negativo ? -(10 ** MAX_DIGITOS) : 10 ** MAX_DIGITOS;
  const n = parseInt(texto, 10);
  return Object.is(n, -0) ? 0 : n;
}

/** Valida el número de nodos introducido por el usuario (7 a 16). */
export function validarNumeroNodos(valor) {
  if (!quitarExteriores(String(valor), ESPACIOS_EXTERIORES)) {
    throw new GrafoError("Debe introducir el número de nodos.");
  }
  const n = leerEntero(valor);
  if (n === null) throw new GrafoError("El número de nodos debe ser un número entero.");
  if (!(NODOS_MINIMO <= n && n <= NODOS_MAXIMO)) {
    throw new GrafoError(`El número de nodos debe estar entre ${NODOS_MINIMO} y ${NODOS_MAXIMO}.`);
  }
  return n;
}

/** Valida un peso introducido por el usuario: entero positivo de 1 a 99. */
export function validarPeso(valor) {
  if (!quitarExteriores(String(valor), ESPACIOS_EXTERIORES)) {
    throw new GrafoError("Debe introducir un peso.");
  }
  const peso = leerEntero(valor);
  if (peso === null) throw new GrafoError("El peso debe ser un número entero.");
  if (peso <= 0) throw new GrafoError("El peso debe ser un entero positivo (no se admite 0 ni negativos).");
  if (peso > PESO_MAXIMO) throw new GrafoError(`El peso debe estar entre ${PESO_MINIMO} y ${PESO_MAXIMO}.`);
  return peso;
}

/** Orden alfabético por código (los vértices son una sola letra mayúscula). */
function porClave(a, b) {
  return a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0;
}

/** Grafo dirigido y ponderado que se mantiene acíclico en todo momento. */
export class Grafo {
  constructor(n) {
    if (!Number.isInteger(n) || !(n >= 1 && n <= NOMBRES_VERTICES.length)) {
      throw new GrafoError(`El grafo admite entre 1 y ${NOMBRES_VERTICES.length} vértices.`);
    }
    this.vertices = NOMBRES_VERTICES.slice(0, n).split("");
    this._salientes = new Map(this.vertices.map((v) => [v, new Map()]));
    this._entrantes = new Map(this.vertices.map((v) => [v, new Map()]));
  }

  // ------------------------------------------------------------------ consulta

  get n() {
    return this.vertices.length;
  }

  existeVertice(v) {
    return this._salientes.has(v);
  }

  _exigirVertice(v) {
    if (!this.existeVertice(v)) throw new GrafoError(`El vértice ${v} no pertenece al grafo.`);
  }

  existeArista(u, v) {
    return this.existeVertice(u) && this._salientes.get(u).has(v);
  }

  peso(u, v) {
    if (!this.existeArista(u, v)) throw new GrafoError(`No existe la arista ${u} → ${v}.`);
    return this._salientes.get(u).get(v);
  }

  /** Aristas que salen de u, ordenadas alfabéticamente por destino: [[destino, peso], …]. */
  salientes(u) {
    this._exigirVertice(u);
    return [...this._salientes.get(u).entries()].sort(porClave);
  }

  /** Aristas que llegan a v, ordenadas alfabéticamente por origen: [[origen, peso], …]. */
  entrantes(v) {
    this._exigirVertice(v);
    return [...this._entrantes.get(v).entries()].sort(porClave);
  }

  /** Todas las aristas [u, v, peso], por origen en orden de vértices y luego por destino. */
  aristas() {
    const salida = [];
    for (const u of this.vertices) {
      for (const [v, p] of [...this._salientes.get(u).entries()].sort(porClave)) salida.push([u, v, p]);
    }
    return salida;
  }

  cantidadAristas() {
    let total = 0;
    for (const d of this._salientes.values()) total += d.size;
    return total;
  }

  /** Indica si existe un camino dirigido de origen a destino. */
  hayCamino(origen, destino) {
    this._exigirVertice(origen);
    this._exigirVertice(destino);
    if (origen === destino) return true;
    const pendientes = [origen];
    const vistos = new Set([origen]);
    while (pendientes.length) {
      const actual = pendientes.pop();
      for (const siguiente of this._salientes.get(actual).keys()) {
        if (siguiente === destino) return true;
        if (!vistos.has(siguiente)) {
          vistos.add(siguiente);
          pendientes.push(siguiente);
        }
      }
    }
    return false;
  }

  /** La arista u → v cerraría un ciclo si v ya alcanza a u. */
  creariaCiclo(u, v) {
    if (u === v) return true;
    return this.hayCamino(v, u);
  }

  /** Verificación independiente de aciclicidad (orden topológico de Kahn). */
  esDag() {
    return this.ordenTopologico().length === this.n;
  }

  /** Orden topológico; si hay ciclo devuelve una lista incompleta. */
  ordenTopologico() {
    const grado = new Map(this.vertices.map((v) => [v, this._entrantes.get(v).size]));
    const disponibles = this.vertices.filter((v) => grado.get(v) === 0).sort();
    const orden = [];
    while (disponibles.length) {
      const actual = disponibles.shift();
      orden.push(actual);
      for (const siguiente of [...this._salientes.get(actual).keys()].sort()) {
        grado.set(siguiente, grado.get(siguiente) - 1);
        if (grado.get(siguiente) === 0) disponibles.push(siguiente);
      }
      disponibles.sort();
    }
    return orden;
  }

  // ---------------------------------------------------------------- modificación

  /** Agrega la arista dirigida u → v. Rechaza duplicados, bucles y ciclos. */
  agregarArista(u, v, peso) {
    this._exigirVertice(u);
    this._exigirVertice(v);
    if (u === v) throw new GrafoError("Un vértice no puede conectarse consigo mismo.");
    if (this.existeArista(u, v)) {
      throw new GrafoError(`La arista ${u} → ${v} ya existe. Puede modificar su peso o eliminarla.`);
    }
    const pesoValido = validarPeso(peso);
    if (this.creariaCiclo(u, v)) {
      throw new GrafoError(
        `La conexión ${u} → ${v} produciría un ciclo, porque ya existe un ` +
          `camino de ${v} hacia ${u}. El grafo debe ser acíclico.`,
      );
    }
    this._salientes.get(u).set(v, pesoValido);
    this._entrantes.get(v).set(u, pesoValido);
  }

  modificarPeso(u, v, peso) {
    if (!this.existeArista(u, v)) throw new GrafoError(`No existe la arista ${u} → ${v}.`);
    const pesoValido = validarPeso(peso);
    this._salientes.get(u).set(v, pesoValido);
    this._entrantes.get(v).set(u, pesoValido);
  }

  eliminarArista(u, v) {
    if (!this.existeArista(u, v)) throw new GrafoError(`No existe la arista ${u} → ${v}.`);
    this._salientes.get(u).delete(v);
    this._entrantes.get(v).delete(u);
  }

  copiar() {
    const copia = new Grafo(this.n);
    for (const [u, v, p] of this.aristas()) {
      copia._salientes.get(u).set(v, p);
      copia._entrantes.get(v).set(u, p);
    }
    return copia;
  }
}

/** Todos los pesos del grafo son enteros dentro del rango admitido. */
export function pesosValidos(grafo) {
  return grafo.aristas().every(([, , p]) => Number.isInteger(p) && PESO_MINIMO <= p && p <= PESO_MAXIMO);
}
