"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import CodeRunner from "@/components/CodeRunner";
import Markdown from "@/components/Markdown";
import Quiz from "@/components/Quiz";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { LessonDetail } from "@/lib/types";

export default function LessonPage({ params }: { params: { id: string } }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api.get<LessonDetail>(`/lessons/${params.id}`).then(setLesson).catch((e) => setError(e.message));
  }, [user, loading, router, params.id]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;
  if (error) return <p className="text-rose-600">{error}</p>;
  if (!lesson) return <p className="text-slate-500">Загрузка урока…</p>;

  return (
    <article>
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{lesson.title}</h1>
        {lesson.progress?.status === "completed" && (
          <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">пройдено</span>
        )}
      </div>

      <Markdown>{lesson.content_md}</Markdown>

      <section className="mt-8">
        <h2 className="mb-2 text-lg font-semibold">Песочница</h2>
        <p className="mb-2 text-sm text-slate-500">
          Попробуйте код прямо в браузере (Python запускается через Pyodide).
        </p>
        <CodeRunner initialCode={'print("Привет, мир!")'} language="python" />
      </section>

      {user.role === "student" && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">Мини-квиз</h2>
          <Quiz lessonId={lesson.id} questions={lesson.questions} />
        </section>
      )}
    </article>
  );
}
