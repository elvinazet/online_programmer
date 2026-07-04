"use client";
import { useState } from "react";

import { api } from "@/lib/api";
import type { PublicQuestion, QuizResult } from "@/lib/types";

import Markdown from "./Markdown";
import { Spinner } from "./ui";

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
    return <p className="muted text-sm">В этом уроке пока нет квиза.</p>;
  }

  return (
    <div className="space-y-4">
      {questions.map((q, i) => {
        const res = resultFor(q.id);
        const ring = res ? (res.is_correct ? "ring-1 ring-[var(--success)]" : "ring-1 ring-[var(--danger)]") : "";
        return (
          <div key={q.id} className={`card p-4 ${ring}`}>
            <div className="mb-3 flex gap-2 font-medium">
              <span className="badge badge-primary h-6 w-6 justify-center rounded-full p-0">{i + 1}</span>
              <div className="flex-1"><Markdown>{q.prompt_md}</Markdown></div>
            </div>

            {(q.type === "single_choice" || q.type === "multiple_choice") && (
              <div className="space-y-1.5">
                {(q.options || []).map((opt, idx) => (
                  <label
                    key={idx}
                    className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-[var(--surface-2)]"
                  >
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
                className="input"
              />
            )}

            {res && (
              <div className="mt-2 text-sm">
                <span className={res.is_correct ? "badge badge-success" : "badge badge-danger"}>
                  {res.is_correct ? "Верно" : "Неверно"}
                </span>
                {res.explanation_md && (
                  <div className="muted mt-1"><Markdown>{res.explanation_md}</Markdown></div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {error && <div className="badge badge-danger px-3 py-2">{error}</div>}

      {!result ? (
        <button onClick={submit} disabled={busy} className="btn btn-primary">
          {busy && <Spinner />} Отправить ответы
        </button>
      ) : (
        <div className={`card p-4 font-medium ${result.passed ? "text-[var(--success)]" : "text-[var(--danger)]"}`}>
          Результат: {result.score}% — {result.passed ? "урок пройден! 🎉" : "нужно ≥ 60%, попробуйте ещё раз"}
        </div>
      )}
    </div>
  );
}
