"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { AttemptDetail, Exam } from "@/lib/types";

export default function ExamsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [exams, setExams] = useState<Exam[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setExams(await api.get<Exam[]>("/exams"));
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [user, loading, router, load]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;

  async function start(examId: number) {
    setError("");
    try {
      const attempt = await api.post<AttemptDetail>(`/exams/${examId}/attempts`);
      router.push(`/attempts/${attempt.id}`);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function createExam() {
    if (!title.trim()) return;
    await api.post("/exams", { title });
    setTitle("");
    load();
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Экзамены</h1>
      {error && <p className="text-rose-600">{error}</p>}

      {user.role === "teacher" && (
        <div className="flex gap-2">
          <input
            placeholder="Название экзамена"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="rounded border border-slate-300 px-3 py-2"
          />
          <button onClick={createExam} className="rounded bg-indigo-600 px-4 py-2 text-white">
            Создать
          </button>
        </div>
      )}

      <div className="space-y-2">
        {exams.map((ex) => (
          <div
            key={ex.id}
            className="flex items-center justify-between rounded border border-slate-200 bg-white p-4"
          >
            <div>
              <div className="font-medium">{ex.title}</div>
              <div className="text-sm text-slate-500">
                {Math.round(ex.duration_seconds / 60)} мин · порог{" "}
                {Math.round(ex.pass_threshold * 100)}%
                {user.role === "teacher" && (ex.is_published ? " · опубликован" : " · черновик")}
              </div>
            </div>
            {user.role === "student" ? (
              <button
                onClick={() => start(ex.id)}
                className="rounded bg-emerald-600 px-4 py-2 text-white"
              >
                Начать
              </button>
            ) : (
              <Link href={`/exams/${ex.id}`} className="text-indigo-600 underline">
                Настроить
              </Link>
            )}
          </div>
        ))}
        {exams.length === 0 && <p className="text-slate-500">Экзаменов пока нет.</p>}
      </div>
    </div>
  );
}
