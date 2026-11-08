import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
export const RUTA_GOLDEN = join(RAIZ, "golden", "dijkstra_golden.json");

export function cargarGolden() {
  return JSON.parse(readFileSync(RUTA_GOLDEN, "utf-8"));
}
