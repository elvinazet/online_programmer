"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { AttemptAnalysis } from "@/lib/types";

import { PageLoader } from "./ui";

function scoreBadge(score: number): string {
  if (score >= 70) return "badge badge-success";
  if (score >= 40) return "badge badge-warning";
  return "badge badge-danger";
}

export default function AnalysisView({ attemptId }: { attemptId: number }) {
  const [analysis, setAnalysis] = useState<AttemptAnalysis | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<AttemptAnalysis>(`/attempts/${attemptId}/analysis`).then(setAnalysis).catch((e) => setError(e.message));
  }, [attemptId]);

  if (error) return <div className="badge badge-danger px-3 py-2">{error}</div>;
  if (!analysis) return <PageLoader label="Загрузка разбора…" />;

  return (
    <div className="space-y-6 text-left">
      <section>
        <h2 className="section-title mb-2">Разбор по темам</h2>
        {analysis.topics.length === 0 ? (
          <p className="muted">Теоретических вопросов не было.</p>
        ) : (
          <div className="space-y-2">
            {analysis.topics.map((t) => (
              <div key={t.module_id} className="card p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{t.module_title}</span>
                  <span className={scoreBadge(t.score)}>{t.score}% ({t.correct}/{t.total})</span>
                </div>
                {t.is_weak && t.lessons.length > 0 && (
                  <div className="mt-2 text-sm">
                    <span className="muted">Повторить: </span>
                    {t.lessons.map((l, i) => (
                      <span key={l.id}>
                        {i > 0 && ", "}
                        <Link href={`/lessons/${l.id}`} className="link">{l.title}</Link>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {analysis.practice.length > 0 && (
        <section>
          <h2 className="section-title mb-1">Тренировочные задачи</h2>
          <p className="muted mb-2 text-sm">Подобраны по слабым темам:</p>
          <div className="card divide-y" style={{ borderColor: "var(--border)" }}>
            {analysis.practice.map((p) => (
              <div key={p.problem_id} className="table-row flex items-center gap-2 px-4 py-2.5 text-sm last:border-0">
                <Link href={`/problems/${p.problem_id}`} className="link font-medium">{p.title}</Link>
                {p.rating && <span className="badge">{p.rating}</span>}
                <span className="muted">{p.tags.join(", ")}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
