"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useToast } from "@/components/Toast";
import { PageHeader, PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ExamHistoryItem, LevelAccess, Stats, TimelinePoint } from "@/lib/types";

const LEVEL_LABEL: Record<string, string> = {
  beginner: "Beginner",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

export default function ProfilePage() {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const [handle, setHandle] = useState("");
  const [avatar, setAvatar] = useState("");
  const [stats, setStats] = useState<Stats | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [levels, setLevels] = useState<LevelAccess[]>([]);
  const [history, setHistory] = useState<ExamHistoryItem[]>([]);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    setHandle(user.student_profile?.codeforces_handle || "");
    setAvatar(user.student_profile?.avatar_url || "");
    if (user.role === "student") {
      api.get<Stats>("/me/stats").then(setStats).catch(() => setStats(null));
      api.get<TimelinePoint[]>("/me/solved-timeline").then(setTimeline).catch(() => setTimeline([]));
      api.get<LevelAccess[]>("/me/level-access").then(setLevels).catch(() => setLevels([]));
      api.get<ExamHistoryItem[]>("/me/exam-history").then(setHistory).catch(() => setHistory([]));
    }
  }, [user, loading, router]);

  if (loading || !user) return <PageLoader />;

  async function saveProfile() {
    try {
      await api.patch("/users/me/student-profile", { codeforces_handle: handle, avatar_url: avatar });
      await refresh();
      toast.success("Профиль сохранён");
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
      setTimeline(await api.get<TimelinePoint[]>("/me/solved-timeline"));
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setSyncing(false);
    }
  }

  const initials = user.email.slice(0, 2).toUpperCase();

  return (
    <div className="space-y-6">
      <PageHeader title="Профиль" subtitle={`${user.email} · ${user.role === "teacher" ? "учитель" : "ученик"}`} />

      {user.role === "student" && (
        <>
          <section className="card flex flex-wrap items-center gap-4 p-5">
            {avatar ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={avatar} alt="avatar" className="h-16 w-16 rounded-full object-cover" />
            ) : (
              <div className="grid h-16 w-16 place-items-center rounded-full surface-2 text-xl font-semibold">{initials}</div>
            )}
            <div className="flex flex-1 flex-wrap items-center gap-2">
              <input placeholder="Codeforces-хэндл" value={handle} onChange={(e) => setHandle(e.target.value)} className="input w-48" />
              <input placeholder="URL аватара" value={avatar} onChange={(e) => setAvatar(e.target.value)} className="input flex-1" style={{ minWidth: "12rem" }} />
              <button onClick={saveProfile} className="btn btn-ghost">Сохранить</button>
              <button onClick={sync} disabled={syncing} className="btn btn-primary">{syncing ? "Синхронизация…" : "Синхронизировать CF"}</button>
            </div>
          </section>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="card p-4 text-center">
              <div className="text-2xl font-semibold">{stats?.solved_total ?? 0}</div>
              <div className="muted text-sm">решено задач</div>
            </div>
            <div className="card p-4 text-center">
              <div className="text-2xl font-semibold">🔥 {stats?.streak ?? 0}</div>
              <div className="muted text-sm">streak, дней</div>
            </div>
            <div className="card p-4 text-center">
              <div className="text-2xl font-semibold">{levels.filter((l) => l.unlocked).length}</div>
              <div className="muted text-sm">открыто уровней</div>
            </div>
            <div className="card p-4 text-center">
              <div className="text-2xl font-semibold">{history.filter((h) => h.passed).length}</div>
              <div className="muted text-sm">сдано экзаменов</div>
            </div>
          </div>

          <section className="card p-5">
            <h2 className="section-title mb-3">Решено задач по времени</h2>
            <TimelineChart points={timeline} />
          </section>

          <section className="card p-5">
            <h2 className="section-title mb-3">Прогресс по темам</h2>
            {stats && Object.keys(stats.by_tag).length > 0 ? (
              <div className="space-y-4">
                <StatBars title="По темам" data={stats.by_tag} />
                <StatBars title="По сложности" data={stats.by_rating} />
              </div>
            ) : (
              <p className="muted">Пока нет данных.</p>
            )}
          </section>

          {levels.length > 0 && (
            <section className="card p-5">
              <h2 className="section-title mb-3">Открытые уровни</h2>
              <div className="flex flex-wrap gap-2">
                {levels.filter((l) => l.unlocked).map((l) => (
                  <span key={l.level_id} className="badge badge-success">
                    {l.course_title}: {LEVEL_LABEL[l.level_name] || l.level_name}
                  </span>
                ))}
                {levels.filter((l) => l.unlocked).length === 0 && <span className="muted text-sm">Пока нет — сдайте экзамен.</span>}
              </div>
            </section>
          )}

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

function TimelineChart({ points }: { points: TimelinePoint[] }) {
  if (points.length === 0) return <p className="muted text-sm">Пока нет решённых задач.</p>;
  const max = Math.max(1, ...points.map((p) => p.count));
  return (
    <div className="flex items-end gap-1" style={{ height: "120px" }}>
      {points.map((p) => (
        <div key={p.date} className="flex flex-1 flex-col items-center justify-end" title={`${p.date}: ${p.count}`}>
          <div className="w-full rounded-t" style={{ height: `${(p.count / max) * 100}%`, minHeight: "4px", background: "var(--primary)" }} />
          <div className="muted mt-1 truncate text-[10px]">{p.date.slice(5)}</div>
        </div>
      ))}
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
