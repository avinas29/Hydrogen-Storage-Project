// Build the handbook: concatenate src/*.html, render KaTeX, build TOC, print to PDF (run twice so TOC page numbers settle).
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const HERE = path.dirname(new URL(import.meta.url).pathname);
const require = createRequire(import.meta.url);
const katex = require("katex");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const OUT_PDF = process.argv[2] || path.join(HERE, "guide.pdf");

const macros = {
  "\\R": "\\mathbb{R}", "\\C": "\\mathbb{C}", "\\one": "\\mathbf{1}", "\\zero": "\\mathbf{0}",
  "\\tr": "\\operatorname{tr}", "\\diag": "\\operatorname{diag}", "\\spec": "\\operatorname{spec}",
  "\\vol": "\\operatorname{vol}", "\\cut": "\\operatorname{cut}", "\\cond": "\\operatorname{cond}",
  "\\nL": "\\mathcal{L}", "\\dist": "\\operatorname{dist}", "\\rank": "\\operatorname{rank}",
  "\\Dh": "D^{-1/2}", "\\Dhp": "D^{1/2}",
};

const files = fs.readdirSync(path.join(HERE, "src")).filter(f => f.endsWith(".html")).sort();
let body = files.map(f => fs.readFileSync(path.join(HERE, "src", f), "utf8")).join("\n");

let mathErrors = 0;
function render(tex, display) {
  try {
    return katex.renderToString(tex, { displayMode: display, throwOnError: true, strict: "ignore", output: "html", macros: { ...macros } });
  } catch (e) {
    mathErrors++;
    console.error("KaTeX error:", e.message.slice(0, 180), "\n   in:", tex.slice(0, 140));
    return `<span style="color:red">${tex}</span>`;
  }
}
body = body.replace(/\\\[([\s\S]+?)\\\]/g, (_, t) => render(t, true));
body = body.replace(/\\\(([\s\S]+?)\\\)([.,;:!?)]?)/g, (_, t, p) => {
  const r = render(t, false);
  return (p && t.length < 70) ? `<span class="nw">${r}${p}</span>` : r + p;
});

const heads = [];
const re = /<h([12])([^>]*)\bid="([^"]+)"[^>]*>([\s\S]*?)<\/h\1>/g;
let m;
while ((m = re.exec(body))) {
  const txt = m[4].replace(/<span class="tg[\s\S]*?<\/span>/g, "").replace(/<\/span>/g, " ").replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
  heads.push({ level: m[1], id: m[3], txt });
}
const ids = heads.map(h => h.id);
const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
if (dup.length) console.error("DUPLICATE IDS:", dup.join(", "));

const pagesFile = path.join(HERE, "pages.json");
const pages = fs.existsSync(pagesFile) ? JSON.parse(fs.readFileSync(pagesFile, "utf8")) : {};
let toc = '<section class="toc"><h1>Contents</h1><div class="cols"><ol>';
for (const h of heads) {
  const cls = h.level === "1" ? "p" : "s";
  toc += `<li class="${cls}"><a href="#${h.id}"><span class="t">${h.txt}</span><span class="dots"></span><span class="pg">${pages[h.id] ?? "00"}</span></a></li>`;
}
toc += "</ol></div></section>";
body = body.replace("<!--TOC-->", toc);
// page references inside text: <a class="pref" href="#id"></a> -> "p. N"
body = body.replace(/<a class="pref" href="#([^"]+)"><\/a>/g, (_, id) => `<a class="pref" href="#${id}">p.&nbsp;${pages[id] ?? "00"}</a>`);

const tpl = fs.readFileSync(path.join(HERE, "template.html"), "utf8");
const htmlPath = path.join(HERE, "guide.html");
fs.writeFileSync(htmlPath, tpl.replace("{{CONTENT}}", body));

execFileSync(CHROME, ["--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--generate-pdf-document-outline",
  `--print-to-pdf=${OUT_PDF}`, `file://${htmlPath}`], { stdio: "pipe" });

const dests = execFileSync("pdfinfo", ["-dests", OUT_PDF]).toString();
const found = {};
for (const line of dests.split("\n")) {
  const mm = line.match(/^\s*(\d+)\s+\[[^\]]*\]\s+"([^"]+)"/);
  if (mm) found[mm[2]] = Number(mm[1]);
}
const missing = heads.filter(h => !(h.id in found)).map(h => h.id);
const changed = Object.keys(found).some(k => pages[k] !== found[k]);
fs.writeFileSync(pagesFile, JSON.stringify(found, null, 1));
const npages = execFileSync("pdfinfo", [OUT_PDF]).toString().match(/Pages:\s+(\d+)/)[1];
console.log(`sections: ${heads.length}, pages: ${npages}, math errors: ${mathErrors}, missing dests: ${missing.length ? missing.slice(0, 8).join(",") : "none"}, page refs changed: ${changed}`);
