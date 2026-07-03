"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import Markdown from "@/components/Markdown";
import SubmitPanel from "@/components/SubmitPanel";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AttemptDetail } from "@/lib/types";

export default function AttemptPage({ params }: { params: { id: string } }) {
  const attemptId = Number(params.id);
  const { user, loading } = useAuth();
  const router = useRouter();
  const [attempt, setAttempt] = useState<AttemptDetail | null>(null);
  const [answers, setAnswers] = useState<Record<number, unknown>>({});
  const [remaining, setRemaining] = useState(0);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const detail = await api.get<AttemptDetail>(`/attempts/${attemptId}`);
    setAttempt(detail);
    setRemaining(detail.remaining_seconds);
    const init: Record<number, unknown> = {};
    for (const q of detail.questions) {
      if (q.student_answer !== null && q.student_answer !== undefined) init[q.id] = q.student_answer;
    }
    setAnswers(init);
  }, [attemptId]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    refresh().catch((e) => setError(e.message));
  }, [user, loading, router, refresh]);

  // серверный таймер: локальный отсчёт, при нуле — перезапрос (сервер завершит)
  useEffect(() => {
    if (!attempt || attempt.status !== "in_progress") return;
    if (remaining <= 0) {
      refresh();
      return;
    }
    const t = setTimeout(() => setRemaining((r) => r - 1), 1000);
    return () => clearTimeout(t);
  }, [attempt, remaining, refresh]);

  // античит: фиксируем потерю/возврат фокуса вкладки
  useEffect(() => {
    if (!attempt || attempt.status !== "in_progress") return;
    const onVis = () => {
      api
        .post(`/attempts/${attemptId}/events`, {
          type: document.hidden ? "focus_lost" : "focus_gained",
        })
        .catch(() => {});
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, [attempt, attemptId]);

  if (loading || !user || !attempt) return <p className="text-slate-500">Загрузка…</p>;

  async function saveAnswers(next: Record<number, unknown>) {
    const payload = {
      answers: attempt!.questions.map((q) => ({
        attempt_question_id: q.id,
        answer: next[q.id] ?? null,
      })),
    };
    try {
      await api.patch(`/attempts/${attemptId}/answers`, payload);
    } catch {
      /* автосохранение best-effort */
    }
  }

  function setAnswer(qid: number, value: unknown) {
    const next = { ...answers, [qid]: value };
    setAnswers(next);
    saveAnswers(next);
  }
  function toggleMulti(qid: number, idx: number) {
    const cur = (answers[qid] as number[]) || [];
    const next = {
      ...answers,
      [qid]: cur.includes(idx) ? cur.filter((i) => i !== idx) : [...cur, idx],
    };
    setAnswers(next);
    saveAnswers(next);
  }

  async function submit() {
    try {
      setAttempt(await api.post<AttemptDetail>(`/attempts/${attemptId}/submit`));
    } catch (e: any) {
      setError(e.message);
    }
  }

  // экран результата
  if (attempt.status !== "in_progress" && attempt.result) {
    const r = attempt.result;
    return (
      <div className="mx-auto max-w-lg text-center">
        <h1 className="mb-3 text-2xl font-semibold">
          {attempt.status === "timed_out" ? "Время вышло" : "Экзамен завершён"}
        </h1>
        <div
          className={`rounded p-4 text-lg ${
            r.passed ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
          }`}
        >
          Итог: {r.total_score}% — {r.passed ? "сдано 🎉" : "не сдано"}
          <div className="mt-2 text-sm text-slate-600">
            Практика: {r.practical_score}% · Теория: {r.theory_score}%
          </div>
          {!r.passed && r.next_retake_allowed_at && (
            <div className="mt-2 text-sm text-slate-500">
              Пересдача после: {new Date(r.next_retake_allowed_at).toLocaleString()}
            </div>
          )}
        </div>
        <Link href="/exams" className="mt-4 inline-block text-indigo-600 underline">
          К экзаменам
        </Link>
      </div>
    );
  }

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
  const ss = String(remaining % 60).padStart(2, "0");
  const lowTime = remaining < 300;

  return (
    <div className="space-y-8">
      <div className="sticky top-0 z-10 -mx-6 flex items-center justify-between border-b border-slate-200 bg-white/90 px-6 py-2 backdrop-blur">
        <span className="font-semibold">Экзамен · попытка {attempt.attempt_number}</span>
        <span className={`font-mono text-lg ${lowTime ? "text-rose-600" : "text-slate-700"}`}>
          {mm}:{ss}
        </span>
      </div>

      {error && <p className="text-rose-600">{error}</p>}

      {attempt.problems.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Практика</h2>
          <div className="space-y-6">
            {attempt.problems.map((p) => (
              <div key={p.id} className="rounded border border-slate-200 p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-medium">{p.title}</span>
                  <span className="text-sm text-slate-500">лучший балл: {p.best_score}%</span>
                </div>
                <SubmitPanel problemId={p.problem_id} attemptId={attemptId} onResult={refresh} />
              </div>
            ))}
          </div>
        </section>
      )}

      {attempt.questions.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Теория</h2>
          <div className="space-y-5">
            {attempt.questions.map((q, i) => (
              <div key={q.id} className="rounded border border-slate-200 p-4">
                <div className="mb-2 font-medium">
                  {i + 1}. <Markdown>{q.prompt_md}</Markdown>
                </div>
                {(q.type === "single_choice" || q.type === "multiple_choice") &&
                  (q.options || []).map((opt, idx) => (
                    <label key={idx} className="flex items-center gap-2">
                      <input
                        type={q.type === "single_choice" ? "radio" : "checkbox"}
                        name={`q-${q.id}`}
                        checked={
                          q.type === "single_choice"
                            ? answers[q.id] === idx
                            : ((answers[q.id] as number[]) || []).includes(idx)
                        }
                        onChange={() =>
                          q.type === "single_choice"
                            ? setAnswer(q.id, idx)
                            : toggleMulti(q.id, idx)
                        }
                      />
                      <span>{opt}</span>
                    </label>
                  ))}
                {(q.type === "short_answer" || q.type === "code_output") && (
                  <input
                    type="text"
                    value={(answers[q.id] as string) || ""}
                    onChange={(e) => setAnswer(q.id, e.target.value)}
                    placeholder="Ваш ответ"
                    className="w-full rounded border border-slate-300 px-3 py-1"
                  />
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <button
        onClick={submit}
        className="rounded bg-indigo-600 px-6 py-2 font-medium text-white"
      >
        Завершить экзамен
      </button>
    </div>
  );
}
