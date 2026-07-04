"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Icon } from "@/components/Icon";
import { PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { CourseTree, ProgressStatus } from "@/lib/types";

const LEVEL_LABELS: Record<string, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

function StatusBadge({ status }: { status: ProgressStatus | null }) {
  if (status === "completed") return <span className="badge badge-success">пройдено</span>;
  if (status === "in_progress") return <span className="badge badge-warning">в процессе</span>;
  return null;
}

export default function CoursePage({ params }: { params: { id: string } }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [course, setCourse] = useState<CourseTree | null>(null);
  const [unlocked, setUnlocked] = useState<Record<number, boolean>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api.get<CourseTree>(`/courses/${params.id}`).then(setCourse).catch((e) => setError(e.message));
    if (user.role === "student") {
      api
        .get<{ level_id: number; unlocked: boolean }[]>("/me/level-access")
        .then((rows) => setUnlocked(Object.fromEntries(rows.map((r) => [r.level_id, r.unlocked]))))
        .catch(() => setUnlocked({}));
    }
  }, [user, loading, router, params.id]);

  if (loading || !user) return <PageLoader />;
  if (error) return <div className="badge badge-danger px-3 py-2">{error}</div>;
  if (!course) return <PageLoader label="Загрузка курса…" />;

  return (
    <div>
      <div className="mb-6 flex items-center gap-3">
        <Link href="/" className="link text-sm">← Курсы</Link>
        <h1 className="page-title">{course.title}</h1>
        <span className="badge badge-primary uppercase">{course.language}</span>
      </div>

      {course.levels.length === 0 && <p className="muted">В курсе пока нет уровней.</p>}

      <div className="space-y-8">
        {course.levels.map((level, idx) => {
          const isTeacher = user.role === "teacher";
          const open = isTeacher || idx === 0 || unlocked[level.id];
          return (
            <section key={level.id}>
              <div className="mb-3 flex items-center gap-2">
                <h2 className="section-title text-[var(--primary)]">
                  {LEVEL_LABELS[level.name] || level.name}
                </h2>
                {!open && <span className="badge badge-warning"><Icon name="lock" className="h-3.5 w-3.5" /> закрыт</span>}
              </div>
              {!open && (
                <p className="muted mb-3 text-sm">
                  Уровень откроется после сдачи экзамена предыдущего уровня.
                </p>
              )}
              <div className="grid grid-cols-1 gap-3">
                {level.modules.map((mod) => (
                  <div key={mod.id} className="card p-4">
                    <div className="mb-2 font-medium">{mod.title}</div>
                    <ul>
                      {mod.lessons.map((lesson) => (
                        <li key={lesson.id} className="table-row flex items-center justify-between py-2 last:border-0">
                          {open ? (
                            <Link href={`/lessons/${lesson.id}`} className="hover:text-[var(--primary)]">
                              {lesson.title}
                            </Link>
                          ) : (
                            <span className="muted">{lesson.title}</span>
                          )}
                          <StatusBadge status={lesson.status} />
                        </li>
                      ))}
                      {mod.lessons.length === 0 && <li className="muted py-2 text-sm">Уроков пока нет</li>}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
