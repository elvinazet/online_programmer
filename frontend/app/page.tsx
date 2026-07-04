"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Course } from "@/lib/types";

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
