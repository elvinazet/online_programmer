/**
 * Копирует движки редактора и рантайма в public/, чтобы отдавать их со своего
 * origin, а не с внешнего CDN (jsdelivr). Тогда песочница и редактор кода
 * работают всегда — включая офлайн и сети с закрытым CDN.
 *
 * Запускается автоматически перед `next build` и `next dev` (см. package.json).
 * Ассеты берутся из node_modules (npm), в git не коммитятся (см. .gitignore).
 */
import { existsSync, mkdirSync, copyFileSync, cpSync, statSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const nm = (p) => resolve(root, "node_modules", p);
const pub = (p) => resolve(root, "public", p);

function copyDir(src, dest, label) {
  if (!existsSync(src)) {
    console.warn(`[assets] пропуск ${label}: не найден ${src} (нужен npm install)`);
    return;
  }
  // уже скопировано и не пусто — не тратим время на пересборках
  if (existsSync(dest) && statSync(dest).isDirectory()) {
    console.log(`[assets] ${label}: уже на месте (${dest})`);
    return;
  }
  mkdirSync(dirname(dest), { recursive: true });
  cpSync(src, dest, { recursive: true });
  console.log(`[assets] ${label}: скопировано → ${dest}`);
}

function copyFiles(srcDir, files, destDir, label) {
  if (!existsSync(srcDir)) {
    console.warn(`[assets] пропуск ${label}: не найден ${srcDir} (нужен npm install)`);
    return;
  }
  mkdirSync(destDir, { recursive: true });
  let n = 0;
  for (const f of files) {
    const s = resolve(srcDir, f);
    if (existsSync(s)) {
      copyFileSync(s, resolve(destDir, f));
      n += 1;
    }
  }
  console.log(`[assets] ${label}: ${n} файл(ов) → ${destDir}`);
}

// Monaco (редактор кода) — весь каталог min/vs
copyDir(nm("monaco-editor/min/vs"), pub("monaco/vs"), "monaco-editor");

// Pyodide (запуск Python в браузере) — только файлы ядра, нужные для рантайма
copyFiles(
  nm("pyodide"),
  ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"],
  pub("pyodide"),
  "pyodide",
);
