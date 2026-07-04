"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Icon } from "@/components/Icon";
import { EmptyState, PageHeader, PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Problem } from "@/lib/types";

export default function ProblemsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [problems, setProblems] = useState<Problem[] | null>(null);
  const [tags, setTags] = useState("");
  const [minRating, setMinRating] = useState("");
  const [maxRating, setMaxRating] = useState("");
  const [solved, setSolved] = useState("");

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (tags.trim()) params.set("tags", tags.trim());
    if (minRating) params.set("min_rating", minRating);
    if (maxRating) params.set("max_rating", maxRating);
    if (solved) params.set("solved", solved);
    setProblems(await api.get<Problem[]>(`/problems?${params.toString()}`));
  }, [tags, minRating, maxRating, solved]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load().catch(() => setProblems([]));
  }, [user, loading, router, load]);

  if (loading || !user) return <PageLoader />;

  return (
    <div>
      <PageHeader
        title="Задачи"
        subtitle="Практика с проверкой в изолированном sandbox"
        actions={
          user.role === "teacher" ? (
            <Link href="/problems/new" className="btn btn-primary btn-sm">+ Создать задачу</Link>
          ) : undefined
        }
      />

      <div className="card mb-5 flex flex-wrap items-end gap-2 p-4">
        <input placeholder="теги через запятую" value={tags} onChange={(e) => setTags(e.target.value)} className="input flex-1" style={{ minWidth: "10rem" }} />
        <input type="number" placeholder="рейтинг от" value={minRating} onChange={(e) => setMinRating(e.target.value)} className="input w-32" />
        <input type="number" placeholder="до" value={maxRating} onChange={(e) => setMaxRating(e.target.value)} className="input w-24" />
        {user.role === "student" && (
          <select value={solved} onChange={(e) => setSolved(e.target.value)} className="select w-40">
            <option value="">все</option>
            <option value="true">решённые</option>
            <option value="false">нерешённые</option>
          </select>
        )}
        <button onClick={() => load()} className="btn btn-primary">Фильтр</button>
      </div>

      {problems === null ? (
        <PageLoader />
      ) : problems.length === 0 ? (
        <EmptyState icon={<Icon name="puzzle" className="h-7 w-7" />} title="Задач не найдено" hint="Измените фильтры или синхронизируйте задачи Codeforces." />
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="table-row muted text-left">
                  <th className="px-4 py-2.5">Задача</th>
                  <th className="px-4 py-2.5">Рейтинг</th>
                  <th className="px-4 py-2.5">Теги</th>
                  <th className="px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                {problems.map((p) => (
                  <tr key={p.id} className="table-row last:border-0 hover:bg-[var(--surface-2)]">
                    <td className="px-4 py-2.5">
                      <Link href={`/problems/${p.id}`} className="font-medium hover:text-[var(--primary)]">{p.title}</Link>
                    </td>
                    <td className="px-4 py-2.5 muted">{p.rating ?? "—"}</td>
                    <td className="px-4 py-2.5 muted">{p.tags.join(", ")}</td>
                    <td className="px-4 py-2.5">{p.solved && <span className="badge badge-success"><Icon name="check" className="h-3.5 w-3.5" strokeWidth={2.5} /> решено</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
