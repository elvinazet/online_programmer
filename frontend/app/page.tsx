"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Course } from "@/lib/types";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [courses, setCourses] = useState<Course[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api.get<Course[]>("/courses").then(setCourses).catch((e) => setError(e.message));
  }, [user, loading, router]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Курсы</h1>
      {error && <p className="text-rose-600">{error}</p>}
      {courses && courses.length === 0 && (
        <p className="text-slate-600">
          Курсов пока нет.{" "}
          {user.role === "teacher" && (
            <Link href="/teach" className="text-indigo-600 underline">
              Создайте первый
            </Link>
          )}
        </p>
      )}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {courses?.map((c) => (
          <Link
            key={c.id}
            href={`/courses/${c.id}`}
            className="rounded border border-slate-200 bg-white p-4 hover:border-indigo-400"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{c.title}</span>
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs uppercase text-slate-600">
                {c.language}
              </span>
            </div>
            {c.description && <p className="mt-1 text-sm text-slate-500">{c.description}</p>}
          </Link>
        ))}
      </div>
    </div>
  );
}
