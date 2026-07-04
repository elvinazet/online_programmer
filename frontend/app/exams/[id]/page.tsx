"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { useToast } from "@/components/Toast";
import { PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AttemptSummary, Exam, ExamTopicAggregate } from "@/lib/types";

export default function ExamManagePage({ params }: { params: { id: string } }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const [exam, setExam] = useState<Exam | null>(null);
  const [attempts, setAttempts] = useState<AttemptSummary[]>([]);
  const [aggregate, setAggregate] = useState<ExamTopicAggregate[]>([]);
  const [problemId, setProblemId] = useState("");
  const [moduleId, setModuleId] = useState("");
  const [numQ, setNumQ] = useState("5");

  const load = useCallback(async () => {
    setExam(await api.get<Exam>(`/exams/${params.id}`));
    setAttempts(await api.get<AttemptSummary[]>(`/exams/${params.id}/attempts`));
    setAggregate(await api.get<ExamTopicAggregate[]>(`/exams/${params.id}/analysis`));
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
    load().catch((e) => toast.error(e.message));
  }, [user, loading, router, load]);

  if (loading || !user) return <PageLoader />;
  if (!exam) return <PageLoader label="Загрузка экзамена…" />;

  async function wrap(fn: () => Promise<void>, okMsg?: string) {
    try {
      await fn();
      if (okMsg) toast.success(okMsg);
      await load();
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/exams" className="link text-sm">← Экзамены</Link>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <h1 className="page-title">{exam.title}</h1>
          <span className={exam.is_published ? "badge badge-success" : "badge badge-warning"}>
            {exam.is_published ? "опубликован" : "черновик"}
          </span>
        </div>
        <p className="muted mt-1 text-sm">
          {Math.round(exam.duration_seconds / 60)} мин · порог {Math.round(exam.pass_threshold * 100)}%
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <section className="card p-5">
          <h2 className="section-title mb-3">Практика</h2>
          <div className="flex flex-wrap gap-2">
            <input placeholder="ID задачи" value={problemId} onChange={(e) => setProblemId(e.target.value)} className="input w-32" />
            <button
              onClick={() => wrap(async () => {
                await api.post(`/exams/${exam!.id}/problems`, { problem_id: Number(problemId) });
                setProblemId("");
              }, "Задача добавлена")}
              className="btn btn-ghost"
            >
              Добавить
            </button>
          </div>
        </section>

        <section className="card p-5">
          <h2 className="section-title mb-3">Теория</h2>
          <div className="flex flex-wrap gap-2">
            <input placeholder="ID модуля" value={moduleId} onChange={(e) => setModuleId(e.target.value)} className="input w-32" />
            <input type="number" placeholder="вопросов" value={numQ} onChange={(e) => setNumQ(e.target.value)} className="input w-28" />
            <button
              onClick={() => wrap(async () => {
                await api.post(`/exams/${exam!.id}/theory`, { module_id: Number(moduleId), num_questions: Number(numQ) });
                setModuleId("");
              }, "Тема добавлена")}
              className="btn btn-ghost"
            >
              Добавить
            </button>
          </div>
        </section>
      </div>

      <button
        onClick={() => wrap(() => api.patch(`/exams/${exam!.id}`, { is_published: !exam!.is_published }),
          exam.is_published ? "Снято с публикации" : "Опубликовано")}
        className="btn btn-primary"
      >
        {exam.is_published ? "Снять с публикации" : "Опубликовать"}
      </button>

      <section>
        <h2 className="section-title mb-2">Результаты</h2>
        {attempts.length === 0 ? (
          <p className="muted">Попыток пока нет.</p>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="table-row muted text-left">
                  <th className="px-4 py-2">Ученик</th><th className="px-4 py-2">Попытка</th>
                  <th className="px-4 py-2">Практика</th><th className="px-4 py-2">Теория</th>
                  <th className="px-4 py-2">Итог</th><th className="px-4 py-2">Статус</th>
                </tr>
              </thead>
              <tbody>
                {attempts.map((a) => (
                  <tr key={a.id} className="table-row last:border-0">
                    <td className="px-4 py-2">#{a.student_id}</td>
                    <td className="px-4 py-2">{a.attempt_number}</td>
                    <td className="px-4 py-2">{a.practical_score}</td>
                    <td className="px-4 py-2">{a.theory_score}</td>
                    <td className="px-4 py-2 font-medium">{a.total_score}%</td>
                    <td className="px-4 py-2">
                      <span className={a.passed ? "badge badge-success" : "badge badge-danger"}>
                        {a.passed ? "сдал" : a.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {aggregate.length > 0 && (
        <section>
          <h2 className="section-title mb-2">Западающие темы группы</h2>
          <div className="card space-y-2 p-4">
            {aggregate.map((a) => (
              <div key={a.module_id} className="flex items-center gap-2 text-sm">
                <span className="muted w-40 shrink-0">{a.module_title}</span>
                <div className="h-2.5 flex-1 rounded-full surface-2">
                  <div className="h-2.5 rounded-full" style={{ width: `${a.score}%`, background: a.is_weak ? "var(--danger)" : "var(--success)" }} />
                </div>
                <span className="w-12 text-right">{a.score}%</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
