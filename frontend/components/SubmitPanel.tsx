"use client";
import dynamic from "next/dynamic";
import { useState } from "react";

import { api } from "@/lib/api";
import type { Submission, SubmissionStatus } from "@/lib/types";

import "./monacoLoader";
import { Spinner } from "./ui";

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
const STATUS_BADGE: Record<SubmissionStatus, string> = {
  queued: "badge",
  running: "badge badge-warning",
  accepted: "badge badge-success",
  wrong_answer: "badge badge-danger",
  tle: "badge badge-danger",
  mle: "badge badge-danger",
  runtime_error: "badge badge-danger",
  compile_error: "badge badge-danger",
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

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <select value={language} onChange={(e) => changeLanguage(e.target.value as "python" | "cpp")} className="select w-40">
          <option value="python">Python</option>
          <option value="cpp">C++</option>
        </select>
        <button onClick={submit} disabled={busy} className="btn btn-primary">
          {busy && <Spinner />} Отправить решение
        </button>
      </div>

      <div className="overflow-hidden rounded-xl border">
        <MonacoEditor
          height="320px"
          language={language}
          value={code}
          onChange={(v) => setCode(v || "")}
          theme="vs-dark"
          options={{ minimap: { enabled: false }, fontSize: 14 }}
        />
      </div>

      {error && <div className="badge badge-danger px-3 py-2">{error}</div>}

      {submission && (
        <div className="card p-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className={STATUS_BADGE[submission.status]}>{STATUS_LABEL[submission.status]}</span>
            {submission.total_tests > 0 && (
              <span className="muted text-sm">
                {submission.passed_tests}/{submission.total_tests} тестов · {submission.score}%
              </span>
            )}
            {submission.time_ms != null && <span className="muted text-sm">{submission.time_ms} мс</span>}
          </div>
          {submission.compile_output && (
            <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-900 p-2 text-xs text-rose-200">
              {submission.compile_output}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
