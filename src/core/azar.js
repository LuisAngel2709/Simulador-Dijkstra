/**
 * Generador de números pseudoaleatorios compatible bit a bit con `random.Random` de Python.
 *
 * Implementa el Mersenne Twister MT19937, la inicialización por semilla entera de CPython
 * (`init_by_array`) y los métodos que usa el generador de grafos: `random`, `getrandbits`,
 * `randint`, `shuffle` y `choice` (mismos algoritmos que CPython 3.11 – 3.13). Con la misma
 * semilla produce exactamente los mismos grafos que la versión Python, lo que permite
 * reproducir los casos de oro sin Pyodide ni servidor.
 */

const N = 624;
const M = 397;
const MATRIX_A = 0x9908b0df;
const UPPER_MASK = 0x80000000;
const LOWER_MASK = 0x7fffffff;

export class AzarPython {
  /** @param {number} [semilla] entero no negativo; sin semilla se usa una aleatoria del sistema. */
  constructor(semilla) {
    this._mt = new Uint32Array(N);
    this._indice = N + 1;
    this.semilla(semilla === undefined ? semillaDelSistema() : semilla);
  }

  semilla(valor) {
    if (!Number.isSafeInteger(valor)) throw new TypeError("La semilla debe ser un entero seguro.");
    // CPython: la clave son los trozos de 32 bits de |semilla|, del menos al más significativo.
    let resto = BigInt(Math.abs(valor));
    const clave = [];
    do {
      clave.push(Number(resto & 0xffffffffn));
      resto >>= 32n;
    } while (resto > 0n);
    this._initByArray(clave);
  }

  _initGenrand(s) {
    const mt = this._mt;
    mt[0] = s >>> 0;
    for (let i = 1; i < N; i++) {
      const previo = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = (Math.imul(1812433253, previo) + i) >>> 0;
    }
    this._indice = N;
  }

  _initByArray(clave) {
    const mt = this._mt;
    this._initGenrand(19650218);
    let i = 1;
    let j = 0;
    for (let k = Math.max(N, clave.length); k > 0; k--) {
      const previo = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = ((mt[i] ^ Math.imul(previo, 1664525)) + clave[j] + j) >>> 0;
      i++;
      j++;
      if (i >= N) {
        mt[0] = mt[N - 1];
        i = 1;
      }
      if (j >= clave.length) j = 0;
    }
    for (let k = N - 1; k > 0; k--) {
      const previo = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = ((mt[i] ^ Math.imul(previo, 1566083941)) - i) >>> 0;
      i++;
      if (i >= N) {
        mt[0] = mt[N - 1];
        i = 1;
      }
    }
    mt[0] = 0x80000000;
    this._indice = N;
  }

  _genrand() {
    const mt = this._mt;
    if (this._indice >= N) {
      let k = 0;
      for (; k < N - M; k++) {
        const y = (mt[k] & UPPER_MASK) | (mt[k + 1] & LOWER_MASK);
        mt[k] = mt[k + M] ^ (y >>> 1) ^ (y & 1 ? MATRIX_A : 0);
      }
      for (; k < N - 1; k++) {
        const y = (mt[k] & UPPER_MASK) | (mt[k + 1] & LOWER_MASK);
        mt[k] = mt[k + (M - N)] ^ (y >>> 1) ^ (y & 1 ? MATRIX_A : 0);
      }
      const y = (mt[N - 1] & UPPER_MASK) | (mt[0] & LOWER_MASK);
      mt[N - 1] = mt[M - 1] ^ (y >>> 1) ^ (y & 1 ? MATRIX_A : 0);
      this._indice = 0;
    }
    let y = mt[this._indice++];
    y ^= y >>> 11;
    y ^= (y << 7) & 0x9d2c5680;
    y ^= (y << 15) & 0xefc60000;
    y ^= y >>> 18;
    return y >>> 0;
  }

  /** Flotante en [0, 1) con 53 bits de precisión, igual que `random.random()`. */
  random() {
    const a = this._genrand() >>> 5;
    const b = this._genrand() >>> 6;
    return (a * 67108864 + b) / 9007199254740992;
  }

  /** Entero de `k` bits aleatorios (0 ≤ k ≤ 32), como `random.getrandbits(k)`. */
  getrandbits(k) {
    if (!Number.isInteger(k) || k < 0 || k > 32) throw new RangeError("getrandbits admite de 0 a 32 bits.");
    if (k === 0) return 0;
    return this._genrand() >>> (32 - k);
  }

  /** Entero en [0, n), como `Random._randbelow` de CPython (n ≥ 1). */
  _randbelow(n) {
    if (!(n >= 1)) return 0;
    const k = 32 - Math.clz32(n); // n.bit_length()
    let r = this.getrandbits(k);
    while (r >= n) r = this.getrandbits(k);
    return r;
  }

  /** Entero en [a, b] (ambos incluidos), como `random.randint`. */
  randint(a, b) {
    return a + this._randbelow(b - a + 1);
  }

  /** Elemento aleatorio de una lista no vacía, como `random.choice`. */
  choice(lista) {
    if (lista.length === 0) throw new RangeError("No se puede elegir de una secuencia vacía.");
    return lista[this._randbelow(lista.length)];
  }

  /** Baraja la lista en el lugar, como `random.shuffle`. */
  shuffle(lista) {
    for (let i = lista.length - 1; i >= 1; i--) {
      const j = this._randbelow(i + 1);
      [lista[i], lista[j]] = [lista[j], lista[i]];
    }
  }
}

function semillaDelSistema() {
  const c = globalThis.crypto;
  if (c && typeof c.getRandomValues === "function") return c.getRandomValues(new Uint32Array(1))[0];
  return Math.floor(Math.random() * 0x100000000);
}
