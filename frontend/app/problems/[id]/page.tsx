"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import Markdown from "@/components/Markdown";
import SubmitPanel from "@/components/SubmitPanel";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ProblemDetail } from "@/lib/types";

export default function ProblemPage({ params }: { params: { id: string } }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api.get<ProblemDetail>(`/problems/${params.id}`).then(setProblem).catch((e) => setError(e.message));
  }, [user, loading, router, params.id]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;
  if (error) return <p className="text-rose-600">{error}</p>;
  if (!problem) return <p className="text-slate-500">Загрузка задачи…</p>;

  return (
    <article>
      <div className="mb-2 flex items-center gap-2">
        <h1 className="text-2xl font-semibold">{problem.title}</h1>
        {problem.solved && <span className="text-emerald-600">✓ решено</span>}
      </div>
      <div className="mb-4 text-sm text-slate-500">
        {problem.rating && <span className="mr-3">Рейтинг: {problem.rating}</span>}
        <span className="mr-3">Лимит: {problem.time_limit_ms} мс</span>
        <span>Память: {problem.memory_limit_mb} МБ</span>
        {problem.url && (
          <a href={problem.url} target="_blank" rel="noreferrer" className="ml-3 text-indigo-600 underline">
            Codeforces ↗
          </a>
        )}
      </div>

      {problem.statement_md && <Markdown>{problem.statement_md}</Markdown>}

      {problem.samples.length > 0 && (
        <section className="mt-6">
          <h2 className="mb-2 text-lg font-semibold">Примеры</h2>
          <div className="space-y-3">
            {problem.samples.map((s, i) => (
              <div key={i} className="grid grid-cols-2 gap-3">
                <div>
                  <div className="mb-1 text-xs text-slate-500">Ввод</div>
                  <pre className="rounded bg-slate-100 p-2 text-sm">{s.input}</pre>
                </div>
                <div>
                  <div className="mb-1 text-xs text-slate-500">Вывод</div>
                  <pre className="rounded bg-slate-100 p-2 text-sm">{s.expected_output}</pre>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {user.role === "student" && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-semibold">Решение</h2>
          <SubmitPanel problemId={problem.id} />
        </section>
      )}
    </article>
  );
}
