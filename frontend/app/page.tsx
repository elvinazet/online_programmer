"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import Burst from "@/components/Burst";
import Landing from "@/components/Landing";
import { PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Assignment } from "@/lib/types";

const QUICK = [
  { href: "/courses", label: "Курсы", icon: "📚", desc: "Учебники C++ и Python" },
  { href: "/problems", label: "Задачи", icon: "🧩", desc: "Практика с проверкой в браузере" },
  { href: "/exams", label: "Экзамены", icon: "🏁", desc: "Контесты на время с разбором" },
];

export default function Home() {
  const { user, loading } = useAuth();
  const [assignments, setAssignments] = useState<Assignment[]>([]);

  useEffect(() => {
    if (!user || user.role !== "student") return;
    api.get<Assignment[]>("/me/assignments").then(setAssignments).catch(() => setAssignments([]));
  }, [user]);

  if (loading) return <PageLoader />;
  if (!user) return <Landing />;

  const pending = assignments.filter((a) => !a.done);

  return (
    <div className="space-y-10">
      <section className="card relative overflow-hidden p-8">
        <Burst points={12} inner={0.42} className="float absolute -right-6 -top-8 h-24 w-24 text-[var(--accent)]" />
        <p className="eyebrow">onproger</p>
        <h1 className="mt-2 text-3xl font-black tracking-tight">
          Привет, {user.email.split("@")[0]} 👋
        </h1>
        <p className="muted mt-2 max-w-xl">
          {user.role === "teacher"
            ? "Создавайте учебники и экзамены, ведите группы и следите за прогрессом учеников."
            : "Учебники, практика на задачах Codeforces и экзамены с разбором — продолжай с того места, где остановился."}
        </p>
      </section>

      {user.role === "student" && pending.length > 0 && (
        <section>
          <h2 className="section-title mb-3">Мои задания</h2>
          <div className="card divide-y" style={{ borderColor: "var(--border)" }}>
            {pending.map((a) => (
              <div key={a.id} className="table-row flex flex-wrap items-center gap-3 px-5 py-3 last:border-0">
                <span className="badge badge-primary">{a.type === "problem" ? "задача" : "глава"}</span>
                <Link
                  href={a.type === "problem" ? `/problems/${a.problem_id}` : `/lessons/${a.lesson_id}`}
                  className="font-bold hover:text-[var(--primary)]"
                >
                  {a.title}
                </Link>
                {a.note && <span className="muted text-sm">· {a.note}</span>}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {QUICK.map((q) => (
          <Link key={q.label} href={q.href} className="card group p-5 transition hover:-translate-y-0.5">
            <div className="text-2xl">{q.icon}</div>
            <div className="mt-3 font-extrabold group-hover:text-[var(--primary)]">{q.label}</div>
            <div className="muted mt-1 text-sm">{q.desc}</div>
          </Link>
        ))}
      </section>
    </div>
  );
}
