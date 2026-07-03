"use client";
import dynamic from "next/dynamic";
import { useState } from "react";

import { api } from "@/lib/api";
import type { Submission, SubmissionStatus } from "@/lib/types";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

const STATUS_LABEL: Record<SubmissionStatus, string> = {
  queued: "В очереди",
  running: "Выполняется",
  accepted: "Принято",
  wrong_answer: "Неверный ответ",
  tle: "Превышено время",
  mle: "Превышена память",
  runtime_error: "Ошибка выполнения",
  compile_error: "Ошибка компиляции",
};

const TERMINAL: SubmissionStatus[] = [
  "accepted", "wrong_answer", "tle", "mle", "runtime_error", "compile_error",
];

const DEFAULT_CODE: Record<string, string> = {
  python: "import sys\n\ndata = sys.stdin.read().split()\n# ваш код\n",
  cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    // ваш код\n    return 0;\n}\n",
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function SubmitPanel({
  problemId,
  attemptId,
  onResult,
}: {
  problemId: number;
  attemptId?: number;
  onResult?: () => void;
}) {
  const [language, setLanguage] = useState<"python" | "cpp">("python");
  const [code, setCode] = useState(DEFAULT_CODE.python);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function changeLanguage(lang: "python" | "cpp") {
    setLanguage(lang);
    if (!code.trim() || code === DEFAULT_CODE.python || code === DEFAULT_CODE.cpp) {
      setCode(DEFAULT_CODE[lang]);
    }
  }

  async function submit() {
    setError("");
    setBusy(true);
    setSubmission(null);
    try {
      const path = attemptId
        ? `/attempts/${attemptId}/problems/${problemId}/submissions`
        : `/problems/${problemId}/submissions`;
      let result = await api.post<Submission>(path, { language, source_code: code });
      setSubmission(result);
      // опрос вердикта (в проде судья асинхронный через Celery)
      let tries = 0;
      while (!TERMINAL.includes(result.status) && tries < 30) {
        await sleep(1200);
        result = await api.get<Submission>(`/submissions/${result.id}`);
        setSubmission(result);
        tries += 1;
      }
      onResult?.();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const accepted = submission?.status === "accepted";

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <select
          value={language}
          onChange={(e) => changeLanguage(e.target.value as "python" | "cpp")}
          className="rounded border border-slate-300 px-3 py-1.5"
        >
          <option value="python">Python</option>
          <option value="cpp">C++</option>
        </select>
        <button
          onClick={submit}
          disabled={busy}
          className="rounded bg-indigo-600 px-4 py-1.5 font-medium text-white disabled:opacity-50"
        >
          {busy ? "Проверяется…" : "Отправить решение"}
        </button>
      </div>

      <div className="overflow-hidden rounded border border-slate-700">
        <MonacoEditor
          height="320px"
          language={language}
          value={code}
          onChange={(v) => setCode(v || "")}
          theme="vs-dark"
          options={{ minimap: { enabled: false }, fontSize: 14 }}
        />
      </div>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      {submission && (
        <div
          className={`rounded p-3 ${
            accepted ? "bg-emerald-50 text-emerald-700" : "bg-slate-50 text-slate-700"
          }`}
        >
          <div className="font-medium">
            {STATUS_LABEL[submission.status]}
            {submission.total_tests > 0 && (
              <span className="ml-2 text-sm">
                ({submission.passed_tests}/{submission.total_tests} тестов, {submission.score}%)
              </span>
            )}
            {submission.time_ms != null && (
              <span className="ml-2 text-sm text-slate-500">{submission.time_ms} мс</span>
            )}
          </div>
          {submission.compile_output && (
            <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-slate-900 p-2 text-xs text-rose-200">
              {submission.compile_output}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
