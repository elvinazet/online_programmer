"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { CourseTree, ProgressStatus } from "@/lib/types";

const LEVEL_LABELS: Record<string, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

function StatusBadge({ status }: { status: ProgressStatus | null }) {
  if (status === "completed")
    return <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">пройдено</span>;
  if (status === "in_progress")
    return <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-700">в процессе</span>;
  return null;
}

export default function CoursePage({ params }: { params: { id: string } }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [course, setCourse] = useState<CourseTree | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api.get<CourseTree>(`/courses/${params.id}`).then(setCourse).catch((e) => setError(e.message));
  }, [user, loading, router, params.id]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;
  if (error) return <p className="text-rose-600">{error}</p>;
  if (!course) return <p className="text-slate-500">Загрузка курса…</p>;

  return (
    <div>
      <div className="mb-4 flex items-center gap-2">
        <h1 className="text-2xl font-semibold">{course.title}</h1>
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs uppercase text-slate-600">
          {course.language}
        </span>
      </div>

      {course.levels.length === 0 && <p className="text-slate-600">В курсе пока нет уровней.</p>}

      <div className="space-y-6">
        {course.levels.map((level) => (
          <section key={level.id}>
            <h2 className="mb-2 text-lg font-semibold text-indigo-700">
              {LEVEL_LABELS[level.name] || level.name}
            </h2>
            <div className="space-y-3">
              {level.modules.map((mod) => (
                <div key={mod.id} className="rounded border border-slate-200 bg-white p-3">
                  <div className="mb-1 font-medium">{mod.title}</div>
                  <ul className="divide-y divide-slate-100">
                    {mod.lessons.map((lesson) => (
                      <li key={lesson.id} className="flex items-center justify-between py-1.5">
                        <Link href={`/lessons/${lesson.id}`} className="text-slate-700 hover:text-indigo-700">
                          {lesson.title}
                        </Link>
                        <StatusBadge status={lesson.status} />
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
