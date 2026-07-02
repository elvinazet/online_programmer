"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import MarkdownEditor from "@/components/MarkdownEditor";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Course, CourseTree, Language } from "@/lib/types";

export default function TeachPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [courses, setCourses] = useState<Course[]>([]);
  const [selected, setSelected] = useState<number | "">("");
  const [tree, setTree] = useState<CourseTree | null>(null);
  const [msg, setMsg] = useState("");

  // формы
  const [cTitle, setCTitle] = useState("");
  const [cLang, setCLang] = useState<Language>("python");
  const [lvlName, setLvlName] = useState("beginner");
  const [modLevel, setModLevel] = useState<number | "">("");
  const [modTitle, setModTitle] = useState("");
  const [lesModule, setLesModule] = useState<number | "">("");
  const [lesTitle, setLesTitle] = useState("");
  const [lesContent, setLesContent] = useState("# Заголовок\n\nТекст урока…");

  const loadCourses = useCallback(async () => {
    setCourses(await api.get<Course[]>("/courses"));
  }, []);

  const loadTree = useCallback(async (id: number) => {
    setTree(await api.get<CourseTree>(`/courses/${id}`));
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role === "teacher") loadCourses().catch((e) => setMsg(e.message));
  }, [user, loading, router, loadCourses]);

  useEffect(() => {
    if (typeof selected === "number") loadTree(selected).catch((e) => setMsg(e.message));
  }, [selected, loadTree]);

  if (loading || !user) return <p className="text-slate-500">Загрузка…</p>;
  if (user.role !== "teacher") return <p className="text-slate-600">Раздел доступен только учителям.</p>;

  async function wrap(fn: () => Promise<void>) {
    setMsg("");
    try {
      await fn();
      if (typeof selected === "number") await loadTree(selected);
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  const modules = tree
    ? tree.levels.flatMap((lvl) =>
        lvl.modules.map((m) => ({ id: m.id, label: `${lvl.name} / ${m.title}` })),
      )
    : [];

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Преподавание</h1>
      {msg && <p className="text-sm text-rose-600">{msg}</p>}

      {/* Создать курс */}
      <section className="rounded border border-slate-200 bg-white p-4">
        <h2 className="mb-3 font-semibold">Новый курс</h2>
        <div className="flex flex-wrap gap-2">
          <input
            placeholder="Название"
            value={cTitle}
            onChange={(e) => setCTitle(e.target.value)}
            className="rounded border border-slate-300 px-3 py-2"
          />
          <select
            value={cLang}
            onChange={(e) => setCLang(e.target.value as Language)}
            className="rounded border border-slate-300 px-3 py-2"
          >
            <option value="python">Python</option>
            <option value="cpp">C++</option>
          </select>
          <button
            onClick={() =>
              wrap(async () => {
                if (!cTitle) return;
                await api.post("/courses", { title: cTitle, language: cLang });
                setCTitle("");
                await loadCourses();
              })
            }
            className="rounded bg-indigo-600 px-4 py-2 text-white"
          >
            Создать
          </button>
        </div>
      </section>

      {/* Выбор курса */}
      <section>
        <label className="mr-2 text-sm text-slate-600">Курс:</label>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value ? Number(e.target.value) : "")}
          className="rounded border border-slate-300 px-3 py-2"
        >
          <option value="">— выберите —</option>
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              {c.title} ({c.language})
            </option>
          ))}
        </select>
      </section>

      {typeof selected === "number" && tree && (
        <>
          {/* Добавить уровень */}
          <section className="rounded border border-slate-200 bg-white p-4">
            <h2 className="mb-3 font-semibold">Добавить уровень</h2>
            <div className="flex gap-2">
              <select
                value={lvlName}
                onChange={(e) => setLvlName(e.target.value)}
                className="rounded border border-slate-300 px-3 py-2"
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
              <button
                onClick={() =>
                  wrap(() => api.post(`/courses/${selected}/levels`, { name: lvlName }))
                }
                className="rounded bg-slate-700 px-4 py-2 text-white"
              >
                Добавить уровень
              </button>
            </div>
          </section>

          {/* Добавить модуль */}
          <section className="rounded border border-slate-200 bg-white p-4">
            <h2 className="mb-3 font-semibold">Добавить модуль</h2>
            <div className="flex flex-wrap gap-2">
              <select
                value={modLevel}
                onChange={(e) => setModLevel(e.target.value ? Number(e.target.value) : "")}
                className="rounded border border-slate-300 px-3 py-2"
              >
                <option value="">— уровень —</option>
                {tree.levels.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
              <input
                placeholder="Название модуля"
                value={modTitle}
                onChange={(e) => setModTitle(e.target.value)}
                className="rounded border border-slate-300 px-3 py-2"
              />
              <button
                onClick={() =>
                  wrap(async () => {
                    if (typeof modLevel !== "number" || !modTitle) return;
                    await api.post(`/levels/${modLevel}/modules`, { title: modTitle });
                    setModTitle("");
                  })
                }
                className="rounded bg-slate-700 px-4 py-2 text-white"
              >
                Добавить модуль
              </button>
            </div>
          </section>

          {/* Добавить урок */}
          <section className="rounded border border-slate-200 bg-white p-4">
            <h2 className="mb-3 font-semibold">Добавить урок</h2>
            <div className="mb-2 flex flex-wrap gap-2">
              <select
                value={lesModule}
                onChange={(e) => setLesModule(e.target.value ? Number(e.target.value) : "")}
                className="rounded border border-slate-300 px-3 py-2"
              >
                <option value="">— модуль —</option>
                {modules.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
              <input
                placeholder="Название урока"
                value={lesTitle}
                onChange={(e) => setLesTitle(e.target.value)}
                className="flex-1 rounded border border-slate-300 px-3 py-2"
              />
            </div>
            <MarkdownEditor value={lesContent} onChange={setLesContent} />
            <button
              onClick={() =>
                wrap(async () => {
                  if (typeof lesModule !== "number" || !lesTitle) return;
                  await api.post(`/modules/${lesModule}/lessons`, {
                    title: lesTitle,
                    content_md: lesContent,
                  });
                  setLesTitle("");
                })
              }
              className="mt-3 rounded bg-indigo-600 px-4 py-2 text-white"
            >
              Сохранить урок
            </button>
          </section>

          {/* Структура курса */}
          <section>
            <h2 className="mb-2 font-semibold">Структура</h2>
            {tree.levels.map((l) => (
              <div key={l.id} className="mb-2">
                <div className="font-medium text-indigo-700">{l.name}</div>
                {l.modules.map((m) => (
                  <div key={m.id} className="ml-4">
                    • {m.title}
                    <span className="ml-2 text-sm text-slate-500">
                      ({m.lessons.map((x) => x.title).join(", ") || "нет уроков"})
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </section>
        </>
      )}
    </div>
  );
}
