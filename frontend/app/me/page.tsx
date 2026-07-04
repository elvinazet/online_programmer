"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useToast } from "@/components/Toast";
import { PageHeader, PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ExamHistoryItem, Stats } from "@/lib/types";

export default function ProfilePage() {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const [handle, setHandle] = useState("");
  const [stats, setStats] = useState<Stats | null>(null);
  const [history, setHistory] = useState<ExamHistoryItem[]>([]);
  const [syncing, setSyncing] = useState(false);

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

  if (loading || !user) return <PageLoader />;

  async function link() {
    try {
      await api.post("/codeforces/link", { handle });
      await refresh();
      toast.success("Хэндл привязан");
    } catch (e: any) {
      toast.error(e.message);
    }
  }
  async function sync() {
    setSyncing(true);
    try {
      const r = await api.post<{ newly_solved: number }>("/codeforces/sync");
      toast.success(`Синхронизировано. Новых решённых: ${r.newly_solved}`);
      setStats(await api.get<Stats>("/me/stats"));
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Профиль"
        subtitle={`${user.email} · ${user.role === "teacher" ? "учитель" : "ученик"}`}
      />

      {user.role === "student" && (
        <>
          <section className="card p-5">
            <h2 className="section-title mb-3">Codeforces</h2>
            <div className="flex flex-wrap gap-2">
              <input placeholder="хэндл" value={handle} onChange={(e) => setHandle(e.target.value)} className="input w-48" />
              <button onClick={link} className="btn btn-ghost">Привязать</button>
              <button onClick={sync} disabled={syncing} className="btn btn-primary">
                {syncing ? "Синхронизация…" : "Синхронизировать решённое"}
              </button>
            </div>
          </section>

          <section className="card p-5">
            <h2 className="section-title mb-3">Прогресс</h2>
            {stats ? (
              <div className="space-y-4">
                <div className="text-lg">Решено задач: <span className="font-semibold">{stats.solved_total}</span></div>
                <StatBars title="По темам" data={stats.by_tag} />
                <StatBars title="По сложности" data={stats.by_rating} />
              </div>
            ) : (
              <p className="muted">Пока нет данных.</p>
            )}
          </section>

          <section className="card p-5">
            <h2 className="section-title mb-3">История экзаменов</h2>
            {history.length === 0 ? (
              <p className="muted">Пока нет завершённых экзаменов.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="table-row muted text-left">
                      <th className="py-2">Экзамен</th><th>Попытка</th><th>Итог</th><th>Статус</th><th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((a) => (
                      <tr key={a.attempt_id} className="table-row last:border-0">
                        <td className="py-2">{a.exam_title}</td>
                        <td>{a.attempt_number}</td>
                        <td className="font-medium">{a.total_score}%</td>
                        <td><span className={a.passed ? "badge badge-success" : "badge badge-danger"}>{a.passed ? "сдан" : "не сдан"}</span></td>
                        <td><Link href={`/attempts/${a.attempt_id}`} className="link">разбор</Link></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
      <div className="muted mb-1 text-sm font-medium">{title}</div>
      <div className="space-y-1.5">
        {entries.map(([label, value]) => (
          <div key={label} className="flex items-center gap-2 text-sm">
            <span className="muted w-28 shrink-0">{label}</span>
            <div className="h-2.5 flex-1 rounded-full surface-2">
              <div className="h-2.5 rounded-full" style={{ width: `${(value / max) * 100}%`, background: "var(--primary)" }} />
            </div>
            <span className="w-8 text-right">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
