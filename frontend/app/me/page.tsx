"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ExamHistoryItem, Stats } from "@/lib/types";

export default function ProfilePage() {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();
  const [handle, setHandle] = useState("");
  const [stats, setStats] = useState<Stats | null>(null);
  const [history, setHistory] = useState<ExamHistoryItem[]>([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    setHandle(user.student_profile?.codeforces_handle || "");
    if (user.role === "student") {
      api.get<Stats>("/me/stats").then(setStats).catch(() => setStats(null));
      api.get<ExamHistoryItem[]>("/me/exam-history").then(setHistory).catch(() => setHistory([]));
    }
  }, [user, loading, router]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;

  async function link() {
    setMsg("");
    try {
      await api.post("/codeforces/link", { handle });
      await refresh();
      setMsg("Хэндл привязан");
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  async function sync() {
    setMsg("");
    try {
      const r = await api.post<{ newly_solved: number }>("/codeforces/sync");
      setMsg(`Синхронизировано. Новых решённых: ${r.newly_solved}`);
      setStats(await api.get<Stats>("/me/stats"));
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Профиль</h1>
        <p className="text-slate-600">
          {user.email} · {user.role === "teacher" ? "учитель" : "ученик"}
        </p>
      </div>

      {user.role === "student" && (
        <>
          <section className="rounded border border-slate-200 bg-white p-4">
            <h2 className="mb-2 font-semibold">Codeforces</h2>
            <div className="flex flex-wrap gap-2">
              <input
                placeholder="хэндл"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                className="rounded border border-slate-300 px-3 py-1.5"
              />
              <button onClick={link} className="rounded bg-slate-700 px-4 py-1.5 text-white">
                Привязать
              </button>
              <button onClick={sync} className="rounded bg-indigo-600 px-4 py-1.5 text-white">
                Синхронизировать решённое
              </button>
            </div>
            {msg && <p className="mt-2 text-sm text-slate-600">{msg}</p>}
          </section>

          <section className="rounded border border-slate-200 bg-white p-4">
            <h2 className="mb-3 font-semibold">Прогресс</h2>
            {stats ? (
              <div className="space-y-3">
                <div className="text-lg">
                  Решено задач: <span className="font-semibold">{stats.solved_total}</span>
                </div>
                <StatBars title="По темам" data={stats.by_tag} />
                <StatBars title="По сложности" data={stats.by_rating} />
              </div>
            ) : (
              <p className="text-slate-500">Пока нет данных.</p>
            )}
          </section>

          <section className="rounded border border-slate-200 bg-white p-4">
            <h2 className="mb-3 font-semibold">История экзаменов</h2>
            {history.length === 0 ? (
              <p className="text-slate-500">Пока нет завершённых экзаменов.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="py-1">Экзамен</th>
                    <th>Попытка</th>
                    <th>Итог</th>
                    <th>Статус</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((a) => (
                    <tr key={a.attempt_id} className="border-b border-slate-100">
                      <td className="py-1">{a.exam_title}</td>
                      <td>{a.attempt_number}</td>
                      <td>{a.total_score}%</td>
                      <td className={a.passed ? "text-emerald-600" : "text-rose-600"}>
                        {a.passed ? "сдан" : "не сдан"}
                      </td>
                      <td>
                        <Link href={`/attempts/${a.attempt_id}`} className="text-indigo-600 underline">
                          разбор
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function StatBars({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  if (entries.length === 0) return null;
  return (
    <div>
      <div className="mb-1 text-sm font-medium text-slate-600">{title}</div>
      <div className="space-y-1">
        {entries.map(([label, value]) => (
          <div key={label} className="flex items-center gap-2 text-sm">
            <span className="w-28 shrink-0 text-slate-500">{label}</span>
            <div className="h-4 flex-1 rounded bg-slate-100">
              <div
                className="h-4 rounded bg-indigo-500"
                style={{ width: `${(value / max) * 100}%` }}
              />
            </div>
            <span className="w-8 text-right">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
