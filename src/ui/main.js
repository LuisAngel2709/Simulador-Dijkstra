import { App } from "./app.js";

const app = new App(document.getElementById("raiz"));
window.__dijkstra = app; // útil para depurar y para las pruebas de interfaz
