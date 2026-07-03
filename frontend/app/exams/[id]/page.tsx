"use client";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AttemptSummary, Exam } from "@/lib/types";

export default function ExamManagePage({ params }: { params: { id: string } }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [exam, setExam] = useState<Exam | null>(null);
  const [attempts, setAttempts] = useState<AttemptSummary[]>([]);
  const [problemId, setProblemId] = useState("");
  const [moduleId, setModuleId] = useState("");
  const [numQ, setNumQ] = useState("5");
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    setExam(await api.get<Exam>(`/exams/${params.id}`));
    setAttempts(await api.get<AttemptSummary[]>(`/exams/${params.id}/attempts`));
  }, [params.id]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role !== "teacher") {
      router.replace("/exams");
      return;
    }
    load().catch((e) => setMsg(e.message));
  }, [user, loading, router, load]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;
  if (!exam) return <p className="text-slate-500">Загрузка экзамена…</p>;

  async function wrap(fn: () => Promise<void>) {
    setMsg("");
    try {
      await fn();
      await load();
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{exam.title}</h1>
        <p className="text-sm text-slate-500">
          {Math.round(exam.duration_seconds / 60)} мин · порог {Math.round(exam.pass_threshold * 100)}% ·{" "}
          {exam.is_published ? "опубликован" : "черновик"}
        </p>
      </div>
      {msg && <p className="text-sm text-rose-600">{msg}</p>}

      <section className="rounded border border-slate-200 bg-white p-4">
        <h2 className="mb-3 font-semibold">Практика</h2>
        <div className="flex flex-wrap gap-2">
          <input
            placeholder="ID задачи"
            value={problemId}
            onChange={(e) => setProblemId(e.target.value)}
            className="w-32 rounded border border-slate-300 px-3 py-2"
          />
          <button
            onClick={() =>
              wrap(async () => {
                await api.post(`/exams/${exam!.id}/problems`, { problem_id: Number(problemId) });
                setProblemId("");
              })
            }
            className="rounded bg-slate-700 px-4 py-2 text-white"
          >
            Добавить задачу
          </button>
        </div>
      </section>

      <section className="rounded border border-slate-200 bg-white p-4">
        <h2 className="mb-3 font-semibold">Теория</h2>
        <div className="flex flex-wrap gap-2">
          <input
            placeholder="ID модуля"
            value={moduleId}
            onChange={(e) => setModuleId(e.target.value)}
            className="w-32 rounded border border-slate-300 px-3 py-2"
          />
          <input
            type="number"
            placeholder="вопросов"
            value={numQ}
            onChange={(e) => setNumQ(e.target.value)}
            className="w-28 rounded border border-slate-300 px-3 py-2"
          />
          <button
            onClick={() =>
              wrap(async () => {
                await api.post(`/exams/${exam!.id}/theory`, {
                  module_id: Number(moduleId),
                  num_questions: Number(numQ),
                });
                setModuleId("");
              })
            }
            className="rounded bg-slate-700 px-4 py-2 text-white"
          >
            Добавить тему
          </button>
        </div>
      </section>

      <button
        onClick={() =>
          wrap(() => api.patch(`/exams/${exam!.id}`, { is_published: !exam!.is_published }))
        }
        className="rounded bg-indigo-600 px-4 py-2 text-white"
      >
        {exam.is_published ? "Снять с публикации" : "Опубликовать"}
      </button>

      <section>
        <h2 className="mb-2 font-semibold">Результаты</h2>
        {attempts.length === 0 ? (
          <p className="text-slate-500">Попыток пока нет.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="py-1">Ученик</th>
                <th>Попытка</th>
                <th>Практика</th>
                <th>Теория</th>
                <th>Итог</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {attempts.map((a) => (
                <tr key={a.id} className="border-b border-slate-100">
                  <td className="py-1">#{a.student_id}</td>
                  <td>{a.attempt_number}</td>
                  <td>{a.practical_score}</td>
                  <td>{a.theory_score}</td>
                  <td>{a.total_score}</td>
                  <td className={a.passed ? "text-emerald-600" : "text-rose-600"}>
                    {a.passed ? "сдал" : a.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
