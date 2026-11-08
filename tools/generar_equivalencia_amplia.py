"""Genera test/fixtures/equivalencia_amplia.json usando el motor Python (fuente de verdad).

Complementa los 32 casos de oro con cientos de grafos más: para cada uno guarda el grafo, la
pareja origen/destino y el SHA-256 de su serialización completa canónica (snapshots, tablas,
explicaciones, tutorial y advertencias). También guarda entradas de validación aleatorias con el
resultado de Python. El motor JavaScript debe reproducir cada hash y cada resultado.

Uso:  python tools/generar_equivalencia_amplia.py [ruta/a/simulador_dijkstra]
No modifica nada de la versión Python: solo la importa.
"""

import hashlib
import json
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
PROYECTO_PY = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI.parent / "simulador_dijkstra"
sys.path.insert(0, str(PROYECTO_PY))

from core.generator import generar_dag, generar_dag_didactico  # noqa: E402
from core.golden import serializar_caso  # noqa: E402
from core.graph import GrafoError, validar_numero_nodos, validar_peso  # noqa: E402


def hash_canonico(caso: dict) -> str:
    texto = json.dumps(caso, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def casos() -> list[dict]:
    salida = []
    for tipo, funcion in (("generado", generar_dag), ("didactico", generar_dag_didactico)):
        for n in range(7, 17):
            for semilla in range(1, 13):
                g, o, d = funcion(n, rng=random.Random(semilla * 100 + n))
                pares = [("normal", o, d), ("primero_ultimo", g.vertices[0], g.vertices[-1]), ("origen_igual_destino", o, o)]
                for etiqueta, a, b in pares:
                    nombre = f"{tipo}_n{n}_s{semilla}_{etiqueta}"
                    salida.append({
                        "nombre": nombre, "tipo": tipo, "n": n, "semilla": semilla * 100 + n,
                        "origen": a, "destino": b,
                        "aristas": [[u, v, p] for u, v, p in g.aristas()],
                        "origen_generado": o, "destino_generado": d,
                        "hash": hash_canonico(serializar_caso(nombre, g, a, b)),
                    })
    return salida


def fuzz_validacion() -> list[dict]:
    azar = random.Random(2026)
    alfabeto = list("0123456789") * 3 + list("+-_ .eExX\t\n\r") + list("٣５１²①") + list("abc")
    salida = []
    for _ in range(600):
        texto = "".join(azar.choice(alfabeto) for _ in range(azar.randint(0, 6)))
        for nombre, f in (("validar_peso", validar_peso), ("validar_numero_nodos", validar_numero_nodos)):
            try:
                valor, error = f(texto), None
            except GrafoError as e:
                valor, error = None, str(e)
            salida.append({"funcion": nombre, "entrada": texto, "valor": valor, "error": error})
    return salida


def main() -> None:
    from core.graph import Grafo  # noqa: F401  (comprueba que el import funciona)
    datos = {"casos": casos(), "validacion": fuzz_validacion()}
    ruta = AQUI / "test" / "fixtures" / "equivalencia_amplia.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{ruta} — {len(datos['casos'])} casos, {len(datos['validacion'])} validaciones, {ruta.stat().st_size // 1024} KiB")


if __name__ == "__main__":
    main()
