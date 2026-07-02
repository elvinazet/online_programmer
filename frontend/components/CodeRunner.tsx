"use client";
import dynamic from "next/dynamic";
import { useState } from "react";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

const PYODIDE_VERSION = "v0.26.2";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/${PYODIDE_VERSION}/full/`;

// Pyodide подгружается из CDN один раз и кэшируется на window.
async function getPyodide(): Promise<any> {
  const w = window as any;
  if (w.__pyodide) return w.__pyodide;
  if (!w.loadPyodide) {
    await new Promise<void>((resolve, reject) => {
      const script = document.createElement("script");
      script.src = `${PYODIDE_URL}pyodide.js`;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Не удалось загрузить Pyodide (нужен интернет)"));
      document.head.appendChild(script);
    });
  }
  w.__pyodide = await w.loadPyodide({ indexURL: PYODIDE_URL });
  return w.__pyodide;
}

export default function CodeRunner({
  initialCode = "",
  language = "python",
}: {
  initialCode?: string;
  language?: "python" | "cpp";
}) {
  const [code, setCode] = useState(initialCode);
  const [output, setOutput] = useState("");
  const [running, setRunning] = useState(false);

  async function run() {
    setRunning(true);
    setOutput("");
    try {
      if (language === "python") {
        const py = await getPyodide();
        py.setStdout({ batched: (s: string) => setOutput((o) => o + s + "\n") });
        py.setStderr({ batched: (s: string) => setOutput((o) => o + s + "\n") });
        await py.runPythonAsync(code);
      } else {
        setOutput(
          "Запуск C++ в браузере не поддерживается. Он появится в разделе задач " +
            "(проверка в серверном sandbox).",
        );
      }
    } catch (e: any) {
      setOutput((o) => o + String(e?.message || e));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="my-4 rounded border border-slate-700 overflow-hidden">
      <MonacoEditor
        height="220px"
        language={language}
        value={code}
        onChange={(v) => setCode(v || "")}
        theme="vs-dark"
        options={{ minimap: { enabled: false }, fontSize: 14 }}
      />
      <div className="flex items-center gap-3 bg-slate-800 px-3 py-2">
        <button
          onClick={run}
          disabled={running}
          className="rounded bg-emerald-600 px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
        >
          {running ? "Выполняется…" : "▶ Запустить"}
        </button>
        <span className="text-xs text-slate-400">{language === "python" ? "Python (Pyodide)" : "C++"}</span>
      </div>
      {output && (
        <pre className="max-h-48 overflow-auto bg-black px-3 py-2 text-sm text-slate-100 whitespace-pre-wrap">
          {output}
        </pre>
      )}
    </div>
  );
}
