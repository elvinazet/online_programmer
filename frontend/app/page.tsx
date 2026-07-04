"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Assignment, Course } from "@/lib/types";

const LANG_BADGE: Record<string, string> = { python: "🐍 Python", cpp: "＋＋ C++" };

const QUICK = [
  { href: "/", label: "Курсы", icon: "📚", desc: "Учебники C++ и Python" },
  { href: "/problems", label: "Задачи", icon: "🧩", desc: "Практика с проверкой в браузере" },
  { href: "/exams", label: "Экзамены", icon: "🏁", desc: "Контесты на время с разбором" },
];

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [assignments, setAssignments] = useState<Assignment[]>([]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api.get<Course[]>("/courses").then(setCourses).catch(() => setCourses([]));
    if (user.role === "student") {
      api.get<Assignment[]>("/me/assignments").then(setAssignments).catch(() => setAssignments([]));
    }
  }, [user, loading, router]);

  if (loading || !user) return <PageLoader />;

  return (
    <div className="space-y-10">
      <section className="card overflow-hidden">
        <div className="bg-gradient-to-br from-[var(--primary)]/10 to-transparent px-7 py-8">
          <h1 className="text-3xl font-semibold tracking-tight">
            Привет, {user.email.split("@")[0]} 👋
          </h1>
          <p className="muted mt-2 max-w-xl">
            Онлайн-школа программирования: учебники, практика на задачах Codeforces
            с проверкой прямо в браузере и экзамены с детальным разбором.
          </p>
        </div>
      </section>

      {user.role === "student" && assignments.filter((a) => !a.done).length > 0 && (
        <section>
          <h2 className="section-title mb-3">Мои задания</h2>
          <div className="card divide-y" style={{ borderColor: "var(--border)" }}>
            {assignments.filter((a) => !a.done).map((a) => (
              <div key={a.id} className="table-row flex items-center gap-3 px-5 py-3 last:border-0">
                <span className="badge badge-primary">{a.type === "problem" ? "задача" : "глава"}</span>
                <Link
                  href={a.type === "problem" ? `/problems/${a.problem_id}` : `/lessons/${a.lesson_id}`}
                  className="flex-1 font-medium hover:text-[var(--primary)]"
                >
                  {a.title}
                </Link>
                {a.note && <span className="muted text-sm">{a.note}</span>}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {QUICK.map((q) => (
          <Link key={q.label} href={q.href} className="card group p-5 transition hover:-translate-y-0.5">
            <div className="text-2xl">{q.icon}</div>
            <div className="mt-3 font-medium group-hover:text-[var(--primary)]">{q.label}</div>
            <div className="muted mt-1 text-sm">{q.desc}</div>
          </Link>
        ))}
      </section>

      <section>
        <h2 className="section-title mb-4">Курсы</h2>
        {courses === null ? (
          <PageLoader />
        ) : courses.length === 0 ? (
          <p className="muted">
            Курсов пока нет.{" "}
            {user.role === "teacher" && (
              <Link href="/teach" className="link">
                Создать первый
              </Link>
            )}
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {courses.map((c) => (
              <Link key={c.id} href={`/courses/${c.id}`} className="card flex items-center justify-between p-5 transition hover:-translate-y-0.5">
                <div>
                  <div className="font-medium">{c.title}</div>
                  {c.description && <div className="muted mt-1 text-sm">{c.description}</div>}
                </div>
                <span className="badge badge-primary">{LANG_BADGE[c.language] || c.language}</span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
