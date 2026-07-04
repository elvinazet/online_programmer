"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState, PageHeader, PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Course } from "@/lib/types";

const LANG_BADGE: Record<string, string> = { python: "🐍 Python", cpp: "＋＋ C++" };

export default function CoursesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [courses, setCourses] = useState<Course[] | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api.get<Course[]>("/courses").then(setCourses).catch(() => setCourses([]));
  }, [user, loading, router]);

  if (loading || !user) return <PageLoader />;

  return (
    <div>
      <PageHeader title="Курсы" subtitle="Учебники C++ и Python — от основ до продвинутого" />
      {courses === null ? (
        <PageLoader />
      ) : courses.length === 0 ? (
        <EmptyState
          icon="📚"
          title="Курсов пока нет"
          hint={user.role === "teacher" ? "Создайте первый курс в разделе «Преподавание»." : "Загляните позже — курсы уже в пути."}
          action={user.role === "teacher" ? <Link href="/teach" className="btn btn-primary btn-sm">В преподавание</Link> : undefined}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {courses.map((c) => (
            <Link key={c.id} href={`/courses/${c.id}`} className="card flex items-center justify-between p-6 transition hover:-translate-y-0.5">
              <div>
                <div className="text-lg font-extrabold">{c.title}</div>
                {c.description && <div className="muted mt-1 text-sm">{c.description}</div>}
              </div>
              <span className="badge badge-accent">{LANG_BADGE[c.language] || c.language}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
