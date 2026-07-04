"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useToast } from "@/components/Toast";
import { PageHeader, PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Group, GroupMember, GroupProgress } from "@/lib/types";

export default function GroupsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const toast = useToast();

  const [groups, setGroups] = useState<Group[]>([]);
  const [selected, setSelected] = useState<number | "">("");
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [progress, setProgress] = useState<GroupProgress[]>([]);

  const [groupName, setGroupName] = useState("");
  const [memberEmail, setMemberEmail] = useState("");

  // форма назначения
  const [target, setTarget] = useState<"group" | "student">("group");
  const [studentId, setStudentId] = useState<number | "">("");
  const [aType, setAType] = useState<"problem" | "lesson">("problem");
  const [refId, setRefId] = useState("");
  const [note, setNote] = useState("");

  const loadGroups = useCallback(async () => {
    setGroups(await api.get<Group[]>("/groups"));
  }, []);
  const loadDetails = useCallback(async (id: number) => {
    setMembers(await api.get<GroupMember[]>(`/groups/${id}/members`));
    setProgress(await api.get<GroupProgress[]>(`/groups/${id}/progress`));
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role !== "teacher") {
      router.replace("/");
      return;
    }
    loadGroups().catch((e) => toast.error(e.message));
  }, [user, loading, router, loadGroups]);

  useEffect(() => {
    if (typeof selected === "number") loadDetails(selected).catch((e) => toast.error(e.message));
  }, [selected, loadDetails]);

  if (loading || !user) return <PageLoader />;

  async function wrap(fn: () => Promise<void>, ok?: string) {
    try {
      await fn();
      if (ok) toast.success(ok);
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  async function assign() {
    const body: Record<string, unknown> = { type: aType, note: note || null };
    if (aType === "problem") body.problem_id = Number(refId);
    else body.lesson_id = Number(refId);
    if (target === "group") body.group_id = selected;
    else body.student_id = studentId;
    await wrap(async () => {
      const r = await api.post<{ message: string }>("/assignments", body);
      setRefId("");
      setNote("");
      toast.success(r.message);
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Группы и задания"
        subtitle="Управляйте учениками, следите за прогрессом, назначайте задачи"
        actions={<Link href="/teach" className="btn btn-ghost btn-sm">← Преподавание</Link>}
      />

      <section className="card flex flex-wrap items-end gap-2 p-5">
        <div className="flex-1">
          <label className="label">Новая группа</label>
          <input placeholder="Название" value={groupName} onChange={(e) => setGroupName(e.target.value)} className="input" />
        </div>
        <button
          onClick={() => wrap(async () => {
            if (!groupName.trim()) return;
            await api.post("/groups", { name: groupName });
            setGroupName("");
            await loadGroups();
          }, "Группа создана")}
          className="btn btn-primary"
        >
          Создать
        </button>
      </section>

      <section className="card p-5">
        <label className="label">Группа</label>
        <select value={selected} onChange={(e) => setSelected(e.target.value ? Number(e.target.value) : "")} className="select">
          <option value="">— выберите —</option>
          {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
        </select>
      </section>

      {typeof selected === "number" && (
        <>
          <section className="card p-5">
            <h2 className="section-title mb-3">Ученики</h2>
            <div className="mb-3 flex flex-wrap gap-2">
              <input placeholder="email ученика" value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} className="input flex-1" />
              <button
                onClick={() => wrap(async () => {
                  await api.post(`/groups/${selected}/members`, { student_email: memberEmail });
                  setMemberEmail("");
                  await loadDetails(selected as number);
                }, "Ученик добавлен")}
                className="btn btn-ghost"
              >
                Добавить
              </button>
            </div>
            {progress.length === 0 ? (
              <p className="muted">В группе пока нет учеников.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="table-row muted text-left">
                      <th className="py-2">Ученик</th><th>Решено</th><th>Уроков</th><th>Экзаменов</th>
                    </tr>
                  </thead>
                  <tbody>
                    {progress.map((p) => (
                      <tr key={p.student_id} className="table-row last:border-0">
                        <td className="py-2">{p.email}</td>
                        <td>{p.solved_total}</td>
                        <td>{p.lessons_completed}</td>
                        <td>{p.exams_passed}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="card p-5">
            <h2 className="section-title mb-3">Назначить задание</h2>
            <div className="flex flex-wrap items-center gap-2">
              <select value={target} onChange={(e) => setTarget(e.target.value as "group" | "student")} className="select w-40">
                <option value="group">Всей группе</option>
                <option value="student">Ученику</option>
              </select>
              {target === "student" && (
                <select value={studentId} onChange={(e) => setStudentId(e.target.value ? Number(e.target.value) : "")} className="select w-56">
                  <option value="">— ученик —</option>
                  {members.map((m) => <option key={m.student_id} value={m.student_id}>{m.email}</option>)}
                </select>
              )}
              <select value={aType} onChange={(e) => setAType(e.target.value as "problem" | "lesson")} className="select w-36">
                <option value="problem">Задача</option>
                <option value="lesson">Глава (урок)</option>
              </select>
              <input placeholder={aType === "problem" ? "ID задачи" : "ID урока"} value={refId} onChange={(e) => setRefId(e.target.value)} className="input w-32" />
              <input placeholder="комментарий (необязательно)" value={note} onChange={(e) => setNote(e.target.value)} className="input flex-1" style={{ minWidth: "12rem" }} />
              <button onClick={assign} className="btn btn-primary">Назначить</button>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
