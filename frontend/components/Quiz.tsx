"use client";
import { useState } from "react";

import { api } from "@/lib/api";
import type { PublicQuestion, QuizResult } from "@/lib/types";

import Markdown from "./Markdown";

export default function Quiz({
  lessonId,
  questions,
  onFinished,
}: {
  lessonId: number;
  questions: PublicQuestion[];
  onFinished?: (r: QuizResult) => void;
}) {
  const [answers, setAnswers] = useState<Record<number, unknown>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const resultFor = (qid: number) => result?.results.find((r) => r.question_id === qid);

  function pickSingle(qid: number, idx: number) {
    setAnswers((a) => ({ ...a, [qid]: idx }));
  }
  function toggleMulti(qid: number, idx: number) {
    setAnswers((a) => {
      const cur = (a[qid] as number[]) || [];
      return { ...a, [qid]: cur.includes(idx) ? cur.filter((i) => i !== idx) : [...cur, idx] };
    });
  }
  function setText(qid: number, val: string) {
    setAnswers((a) => ({ ...a, [qid]: val }));
  }

  async function submit() {
    setError("");
    setBusy(true);
    try {
      const payload = {
        answers: questions.map((q) => ({
          question_id: q.id,
          answer: answers[q.id] ?? (q.type === "multiple_choice" ? [] : ""),
        })),
      };
      const r = await api.post<QuizResult>(`/lessons/${lessonId}/quiz`, payload);
      setResult(r);
      onFinished?.(r);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (questions.length === 0) {
    return <p className="text-sm text-slate-500">В этом уроке пока нет квиза.</p>;
  }

  return (
    <div className="space-y-6">
      {questions.map((q, i) => {
        const res = resultFor(q.id);
        const border = res ? (res.is_correct ? "border-emerald-500" : "border-rose-500") : "border-slate-200";
        return (
          <div key={q.id} className={`rounded border ${border} p-4`}>
            <div className="mb-2 font-medium">
              {i + 1}. <span className="inline-block"><Markdown>{q.prompt_md}</Markdown></span>
            </div>

            {(q.type === "single_choice" || q.type === "multiple_choice") && (
              <div className="space-y-1">
                {(q.options || []).map((opt, idx) => (
                  <label key={idx} className="flex items-center gap-2">
                    <input
                      type={q.type === "single_choice" ? "radio" : "checkbox"}
                      name={`q-${q.id}`}
                      disabled={!!result}
                      checked={
                        q.type === "single_choice"
                          ? answers[q.id] === idx
                          : ((answers[q.id] as number[]) || []).includes(idx)
                      }
                      onChange={() =>
                        q.type === "single_choice" ? pickSingle(q.id, idx) : toggleMulti(q.id, idx)
                      }
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            )}

            {(q.type === "short_answer" || q.type === "code_output") && (
              <input
                type="text"
                disabled={!!result}
                value={(answers[q.id] as string) || ""}
                onChange={(e) => setText(q.id, e.target.value)}
                placeholder={q.type === "code_output" ? "Что выведет код?" : "Ваш ответ"}
                className="w-full rounded border border-slate-300 px-3 py-1"
              />
            )}

            {res && (
              <div className="mt-2 text-sm">
                <span className={res.is_correct ? "text-emerald-600" : "text-rose-600"}>
                  {res.is_correct ? "Верно" : "Неверно"}
                </span>
                {res.explanation_md && (
                  <div className="mt-1 text-slate-600">
                    <Markdown>{res.explanation_md}</Markdown>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {error && <p className="text-sm text-rose-600">{error}</p>}

      {!result ? (
        <button
          onClick={submit}
          disabled={busy}
          className="rounded bg-indigo-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {busy ? "Проверяем…" : "Отправить ответы"}
        </button>
      ) : (
        <div
          className={`rounded p-3 font-medium ${
            result.passed ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
          }`}
        >
          Результат: {result.score}% — {result.passed ? "урок пройден!" : "нужно ≥ 60%, попробуйте ещё раз"}
        </div>
      )}
    </div>
  );
}
