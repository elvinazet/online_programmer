"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { AttemptAnalysis } from "@/lib/types";

function scoreColor(score: number): string {
  if (score >= 70) return "bg-emerald-100 text-emerald-800";
  if (score >= 40) return "bg-amber-100 text-amber-800";
  return "bg-rose-100 text-rose-800";
}

export default function AnalysisView({ attemptId }: { attemptId: number }) {
  const [analysis, setAnalysis] = useState<AttemptAnalysis | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<AttemptAnalysis>(`/attempts/${attemptId}/analysis`)
      .then(setAnalysis)
      .catch((e) => setError(e.message));
  }, [attemptId]);

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!analysis) return <p className="text-slate-500">Загрузка разбора…</p>;

  return (
    <div className="space-y-6 text-left">
      <section>
        <h2 className="mb-2 text-lg font-semibold">Разбор по темам</h2>
        {analysis.topics.length === 0 ? (
          <p className="text-slate-500">Теоретических вопросов не было.</p>
        ) : (
          <div className="space-y-2">
            {analysis.topics.map((t) => (
              <div key={t.module_id} className="rounded border border-slate-200 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{t.module_title}</span>
                  <span className={`rounded px-2 py-0.5 text-sm ${scoreColor(t.score)}`}>
                    {t.score}% ({t.correct}/{t.total})
                  </span>
                </div>
                {t.is_weak && t.lessons.length > 0 && (
                  <div className="mt-2 text-sm">
                    <span className="text-slate-500">Повторить: </span>
                    {t.lessons.map((l, i) => (
                      <span key={l.id}>
                        {i > 0 && ", "}
                        <Link href={`/lessons/${l.id}`} className="text-indigo-600 underline">
                          {l.title}
                        </Link>
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
          <h2 className="mb-2 text-lg font-semibold">Тренировочные задачи</h2>
          <p className="mb-2 text-sm text-slate-500">Подобраны по слабым темам:</p>
          <ul className="space-y-1">
            {analysis.practice.map((p) => (
              <li key={p.problem_id} className="flex items-center gap-2 text-sm">
                <Link href={`/problems/${p.problem_id}`} className="text-indigo-600 underline">
                  {p.title}
                </Link>
                {p.rating && <span className="text-slate-400">{p.rating}</span>}
                <span className="text-slate-400">{p.tags.join(", ")}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
