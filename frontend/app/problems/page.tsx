"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Problem } from "@/lib/types";

export default function ProblemsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [problems, setProblems] = useState<Problem[]>([]);
  const [tags, setTags] = useState("");
  const [minRating, setMinRating] = useState("");
  const [maxRating, setMaxRating] = useState("");
  const [solved, setSolved] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    const params = new URLSearchParams();
    if (tags.trim()) params.set("tags", tags.trim());
    if (minRating) params.set("min_rating", minRating);
    if (maxRating) params.set("max_rating", maxRating);
    if (solved) params.set("solved", solved);
    try {
      setProblems(await api.get<Problem[]>(`/problems?${params.toString()}`));
    } catch (e: any) {
      setError(e.message);
    }
  }, [tags, minRating, maxRating, solved]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [user, loading, router, load]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Задачи</h1>

      <div className="mb-4 flex flex-wrap items-end gap-2">
        <input
          placeholder="теги через запятую"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          className="rounded border border-slate-300 px-3 py-1.5"
        />
        <input
          type="number"
          placeholder="рейтинг от"
          value={minRating}
          onChange={(e) => setMinRating(e.target.value)}
          className="w-28 rounded border border-slate-300 px-3 py-1.5"
        />
        <input
          type="number"
          placeholder="до"
          value={maxRating}
          onChange={(e) => setMaxRating(e.target.value)}
          className="w-24 rounded border border-slate-300 px-3 py-1.5"
        />
        {user.role === "student" && (
          <select
            value={solved}
            onChange={(e) => setSolved(e.target.value)}
            className="rounded border border-slate-300 px-3 py-1.5"
          >
            <option value="">все</option>
            <option value="true">решённые</option>
            <option value="false">нерешённые</option>
          </select>
        )}
        <button onClick={load} className="rounded bg-indigo-600 px-4 py-1.5 text-white">
          Фильтр
        </button>
      </div>

      {error && <p className="text-rose-600">{error}</p>}

      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-slate-500">
            <th className="py-2">Задача</th>
            <th className="py-2">Рейтинг</th>
            <th className="py-2">Теги</th>
            <th className="py-2"></th>
          </tr>
        </thead>
        <tbody>
          {problems.map((p) => (
            <tr key={p.id} className="border-b border-slate-100">
              <td className="py-2">
                <Link href={`/problems/${p.id}`} className="text-indigo-700 hover:underline">
                  {p.title}
                </Link>
              </td>
              <td className="py-2">{p.rating ?? "—"}</td>
              <td className="py-2 text-slate-500">{p.tags.join(", ")}</td>
              <td className="py-2">
                {p.solved && <span className="text-emerald-600">✓ решено</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {problems.length === 0 && <p className="mt-3 text-slate-500">Задач не найдено.</p>}
    </div>
  );
}
