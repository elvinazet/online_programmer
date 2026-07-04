"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import CodeRunner from "@/components/CodeRunner";
import Markdown from "@/components/Markdown";
import Quiz from "@/components/Quiz";
import { PageLoader } from "@/components/ui";
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

  if (loading || !user) return <PageLoader />;
  if (error) return <div className="badge badge-danger px-3 py-2">{error}</div>;
  if (!lesson) return <PageLoader label="Загрузка урока…" />;

  return (
    <article className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="page-title">{lesson.title}</h1>
        {lesson.progress?.status === "completed" && <span className="badge badge-success">пройдено</span>}
      </div>

      <div className="card p-6">
        <Markdown>{lesson.content_md}</Markdown>
      </div>

      <section>
        <h2 className="section-title mb-1">Песочница</h2>
        <p className="muted mb-3 text-sm">Запустите Python прямо в браузере (Pyodide).</p>
        <CodeRunner initialCode={'print("Привет, мир!")'} language="python" />
      </section>

      {user.role === "student" && (
        <section>
          <h2 className="section-title mb-3">Мини-квиз</h2>
          <Quiz lessonId={lesson.id} questions={lesson.questions} />
        </section>
      )}

      <Link href="/" className="link inline-block text-sm">← К курсам</Link>
    </article>
  );
}
