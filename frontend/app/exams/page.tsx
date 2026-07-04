"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Icon } from "@/components/Icon";
import { useToast } from "@/components/Toast";
import { EmptyState, PageHeader, PageLoader, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AttemptDetail, Exam } from "@/lib/types";

export default function ExamsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const [exams, setExams] = useState<Exam[] | null>(null);
  const [title, setTitle] = useState("");
  const [starting, setStarting] = useState<number | null>(null);

  const load = useCallback(async () => {
    setExams(await api.get<Exam[]>("/exams"));
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load().catch(() => setExams([]));
  }, [user, loading, router, load]);

  if (loading || !user) return <PageLoader />;

  async function start(examId: number) {
    setStarting(examId);
    try {
      const attempt = await api.post<AttemptDetail>(`/exams/${examId}/attempts`);
      router.push(`/attempts/${attempt.id}`);
    } catch (e: any) {
      toast.error(e.message);
      setStarting(null);
    }
  }

  async function createExam() {
    if (!title.trim()) return;
    await api.post("/exams", { title });
    setTitle("");
    toast.success("Экзамен создан");
    load();
  }

  return (
    <div>
      <PageHeader title="Экзамены" subtitle="Контесты на время: практика + теория с разбором" />

      {user.role === "teacher" && (
        <div className="card mb-5 flex gap-2 p-4">
          <input placeholder="Название нового экзамена" value={title} onChange={(e) => setTitle(e.target.value)} className="input flex-1" />
          <button onClick={createExam} className="btn btn-primary">Создать</button>
        </div>
      )}

      {exams === null ? (
        <PageLoader />
      ) : exams.length === 0 ? (
        <EmptyState icon={<Icon name="flag" className="h-7 w-7" />} title="Экзаменов пока нет" />
      ) : (
        <div className="space-y-3">
          {exams.map((ex) => (
            <div key={ex.id} className="card flex items-center justify-between p-5">
              <div>
                <div className="font-medium">{ex.title}</div>
                <div className="muted mt-1 flex flex-wrap gap-2 text-sm">
                  <span className="badge">{Math.round(ex.duration_seconds / 60)} мин</span>
                  <span className="badge">порог {Math.round(ex.pass_threshold * 100)}%</span>
                  {user.role === "teacher" && (
                    <span className={ex.is_published ? "badge badge-success" : "badge badge-warning"}>
                      {ex.is_published ? "опубликован" : "черновик"}
                    </span>
                  )}
                </div>
              </div>
              {user.role === "student" ? (
                <button onClick={() => start(ex.id)} disabled={starting === ex.id} className="btn btn-success">
                  {starting === ex.id && <Spinner />} Начать
                </button>
              ) : (
                <Link href={`/exams/${ex.id}`} className="btn btn-ghost">Настроить</Link>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
