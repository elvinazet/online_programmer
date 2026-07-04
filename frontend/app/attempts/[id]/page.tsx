"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import AnalysisView from "@/components/AnalysisView";
import Markdown from "@/components/Markdown";
import SubmitPanel from "@/components/SubmitPanel";
import { PageLoader } from "@/components/ui";
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

  useEffect(() => {
    if (!attempt || attempt.status !== "in_progress") return;
    if (remaining <= 0) {
      refresh();
      return;
    }
    const t = setTimeout(() => setRemaining((r) => r - 1), 1000);
    return () => clearTimeout(t);
  }, [attempt, remaining, refresh]);

  useEffect(() => {
    if (!attempt || attempt.status !== "in_progress") return;
    const onVis = () => {
      api.post(`/attempts/${attemptId}/events`, {
        type: document.hidden ? "focus_lost" : "focus_gained",
      }).catch(() => {});
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, [attempt, attemptId]);

  if (loading || !user || !attempt) return <PageLoader />;

  async function saveAnswers(next: Record<number, unknown>) {
    const payload = {
      answers: attempt!.questions.map((q) => ({ attempt_question_id: q.id, answer: next[q.id] ?? null })),
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
    const next = { ...answers, [qid]: cur.includes(idx) ? cur.filter((i) => i !== idx) : [...cur, idx] };
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

  if (attempt.status !== "in_progress" && attempt.result) {
    const r = attempt.result;
    return (
      <div className="mx-auto max-w-2xl">
        <h1 className="page-title mb-3 text-center">
          {attempt.status === "timed_out" ? "Время вышло" : "Экзамен завершён"}
        </h1>
        <div className={`card p-5 text-center text-lg ${r.passed ? "text-[var(--success)]" : "text-[var(--danger)]"}`}>
          Итог: {r.total_score}% — {r.passed ? "сдано 🎉" : "не сдано"}
          <div className="muted mt-2 text-sm">Практика: {r.practical_score}% · Теория: {r.theory_score}%</div>
          {!r.passed && r.next_retake_allowed_at && (
            <div className="muted mt-2 text-sm">Пересдача после: {new Date(r.next_retake_allowed_at).toLocaleString()}</div>
          )}
        </div>
        <div className="mt-6"><AnalysisView attemptId={attemptId} /></div>
        <Link href="/exams" className="link mt-6 inline-block text-sm">← К экзаменам</Link>
      </div>
    );
  }

  const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
  const ss = String(remaining % 60).padStart(2, "0");
  const lowTime = remaining < 300;

  return (
    <div className="space-y-8">
      <div className="nav-blur sticky top-16 z-20 -mx-5 flex items-center justify-between border-y px-5 py-2.5">
        <span className="font-semibold">Экзамен · попытка {attempt.attempt_number}</span>
        <span className={`font-mono text-lg ${lowTime ? "text-[var(--danger)]" : ""}`}>{mm}:{ss}</span>
      </div>

      {error && <div className="badge badge-danger px-3 py-2">{error}</div>}

      {attempt.problems.length > 0 && (
        <section>
          <h2 className="section-title mb-3">Практика</h2>
          <div className="space-y-6">
            {attempt.problems.map((p) => (
              <div key={p.id} className="card p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-medium">{p.title}</span>
                  <span className="badge">лучший балл: {p.best_score}%</span>
                </div>
                <SubmitPanel problemId={p.problem_id} attemptId={attemptId} onResult={refresh} />
              </div>
            ))}
          </div>
        </section>
      )}

      {attempt.questions.length > 0 && (
        <section>
          <h2 className="section-title mb-3">Теория</h2>
          <div className="space-y-4">
            {attempt.questions.map((q, i) => (
              <div key={q.id} className="card p-4">
                <div className="mb-2 flex gap-2 font-medium">
                  <span className="badge badge-primary h-6 w-6 justify-center rounded-full p-0">{i + 1}</span>
                  <div className="flex-1"><Markdown>{q.prompt_md}</Markdown></div>
                </div>
                {(q.type === "single_choice" || q.type === "multiple_choice") &&
                  (q.options || []).map((opt, idx) => (
                    <label key={idx} className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-[var(--surface-2)]">
                      <input
                        type={q.type === "single_choice" ? "radio" : "checkbox"}
                        name={`q-${q.id}`}
                        checked={q.type === "single_choice" ? answers[q.id] === idx : ((answers[q.id] as number[]) || []).includes(idx)}
                        onChange={() => (q.type === "single_choice" ? setAnswer(q.id, idx) : toggleMulti(q.id, idx))}
                      />
                      <span>{opt}</span>
                    </label>
                  ))}
                {(q.type === "short_answer" || q.type === "code_output") && (
                  <input type="text" value={(answers[q.id] as string) || ""} onChange={(e) => setAnswer(q.id, e.target.value)} placeholder="Ваш ответ" className="input" />
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <button onClick={submit} className="btn btn-primary px-6">Завершить экзамен</button>
    </div>
  );
}
