"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Icon } from "@/components/Icon";
import Markdown from "@/components/Markdown";
import SubmitPanel from "@/components/SubmitPanel";
import { PageLoader } from "@/components/ui";
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

  if (loading || !user) return <PageLoader />;
  if (error) return <div className="badge badge-danger px-3 py-2">{error}</div>;
  if (!problem) return <PageLoader label="Загрузка задачи…" />;

  return (
    <article className="space-y-6">
      <div>
        <Link href="/problems" className="link text-sm">← Задачи</Link>
        <div className="mt-2 flex items-center gap-2">
          <h1 className="page-title">{problem.title}</h1>
          {problem.solved && (
            <span className="badge badge-success">
              <Icon name="check" className="h-3.5 w-3.5" strokeWidth={2.5} /> решено
            </span>
          )}
        </div>
        <div className="muted mt-2 flex flex-wrap gap-3 text-sm">
          {problem.rating && <span className="badge">рейтинг {problem.rating}</span>}
          <span className="badge"><Icon name="clock" className="h-3.5 w-3.5" /> {problem.time_limit_ms} мс</span>
          <span className="badge"><Icon name="chip" className="h-3.5 w-3.5" /> {problem.memory_limit_mb} МБ</span>
          {problem.tags.map((t) => <span key={t} className="badge badge-primary">{t}</span>)}
          {problem.url && <a href={problem.url} target="_blank" rel="noreferrer" className="link">Codeforces ↗</a>}
        </div>
      </div>

      {problem.statement_md && <div className="card p-6"><Markdown>{problem.statement_md}</Markdown></div>}

      {problem.samples.length > 0 && (
        <section>
          <h2 className="section-title mb-2">Примеры</h2>
          <div className="space-y-3">
            {problem.samples.map((s, i) => (
              <div key={i} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="card p-3">
                  <div className="muted mb-1 text-xs">Ввод</div>
                  <pre className="overflow-auto text-sm">{s.input}</pre>
                </div>
                <div className="card p-3">
                  <div className="muted mb-1 text-xs">Вывод</div>
                  <pre className="overflow-auto text-sm">{s.expected_output}</pre>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {user.role === "student" && (
        <section>
          <h2 className="section-title mb-3">Решение</h2>
          <SubmitPanel problemId={problem.id} />
        </section>
      )}
    </article>
  );
}
