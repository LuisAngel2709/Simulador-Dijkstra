import http from "node:http"; import fs from "node:fs"; import path from "node:path";
const raiz = path.resolve(process.argv[2]); const puerto = +process.argv[3] || 8123;
const tipos = {".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8",".json":"application/json"};
http.createServer((q,r)=>{let p=path.join(raiz,decodeURIComponent(q.url.split("?")[0]));if(p.endsWith("/"))p+="index.html";
fs.readFile(p,(e,d)=>{if(e){r.writeHead(404);r.end("404");return;}r.writeHead(200,{"Content-Type":tipos[path.extname(p)]||"application/octet-stream"});r.end(d);});}).listen(puerto,()=>console.log("ok",puerto));
