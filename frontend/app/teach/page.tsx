"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import MarkdownEditor from "@/components/MarkdownEditor";
import TeacherContent from "@/components/TeacherContent";
import { useToast } from "@/components/Toast";
import { PageHeader, PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Course, CourseTree, Language, LessonDetail } from "@/lib/types";

export default function TeachPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const toast = useToast();

  const [courses, setCourses] = useState<Course[]>([]);
  const [selected, setSelected] = useState<number | "">("");
  const [tree, setTree] = useState<CourseTree | null>(null);

  const [cTitle, setCTitle] = useState("");
  const [cLang, setCLang] = useState<Language>("python");
  const [lvlName, setLvlName] = useState("beginner");
  const [modLevel, setModLevel] = useState<number | "">("");
  const [modTitle, setModTitle] = useState("");
  const [lesModule, setLesModule] = useState<number | "">("");
  const [lesTitle, setLesTitle] = useState("");
  const [lesContent, setLesContent] = useState("# Заголовок\n\nТекст урока…");
  const [editLesson, setEditLesson] = useState<number | "">("");
  const [editTitle, setEditTitle] = useState("");
  const [editContent, setEditContent] = useState("");

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
    if (user.role === "teacher") loadCourses().catch((e) => toast.error(e.message));
  }, [user, loading, router, loadCourses]);

  useEffect(() => {
    if (typeof selected === "number") loadTree(selected).catch((e) => toast.error(e.message));
  }, [selected, loadTree]);

  useEffect(() => {
    if (typeof editLesson !== "number") return;
    api.get<LessonDetail>(`/lessons/${editLesson}`).then((l) => {
      setEditTitle(l.title);
      setEditContent(l.content_md);
    }).catch((e) => toast.error(e.message));
  }, [editLesson]);

  if (loading || !user) return <PageLoader />;
  if (user.role !== "teacher") return <p className="muted">Раздел доступен только учителям.</p>;

  const lessonsFlat = tree
    ? tree.levels.flatMap((lvl) => lvl.modules.flatMap((m) => m.lessons.map((les) => ({ id: les.id, label: `${m.title} / ${les.title}` }))))
    : [];

  async function wrap(fn: () => Promise<void>, okMsg?: string) {
    try {
      await fn();
      if (typeof selected === "number") await loadTree(selected);
      if (okMsg) toast.success(okMsg);
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  const modules = tree
    ? tree.levels.flatMap((lvl) => lvl.modules.map((m) => ({ id: m.id, label: `${lvl.name} / ${m.title}` })))
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Преподавание"
        subtitle="Создавайте курсы, уроки и квизы"
        actions={<Link href="/teach/groups" className="btn btn-ghost btn-sm">Группы и задания →</Link>}
      />

      <section className="card p-5">
        <h2 className="section-title mb-3">Новый курс</h2>
        <div className="flex flex-wrap gap-2">
          <input placeholder="Название" value={cTitle} onChange={(e) => setCTitle(e.target.value)} className="input flex-1" />
          <select value={cLang} onChange={(e) => setCLang(e.target.value as Language)} className="select w-36">
            <option value="python">Python</option>
            <option value="cpp">C++</option>
          </select>
          <button
            onClick={() => wrap(async () => {
              if (!cTitle) return;
              await api.post("/courses", { title: cTitle, language: cLang });
              setCTitle("");
              await loadCourses();
            }, "Курс создан")}
            className="btn btn-primary"
          >
            Создать
          </button>
        </div>
      </section>

      <section className="card p-5">
        <label className="label">Курс для редактирования</label>
        <select value={selected} onChange={(e) => setSelected(e.target.value ? Number(e.target.value) : "")} className="select">
          <option value="">— выберите —</option>
          {courses.map((c) => <option key={c.id} value={c.id}>{c.title} ({c.language})</option>)}
        </select>
      </section>

      {typeof selected === "number" && tree && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <section className="card p-5">
              <h2 className="section-title mb-3">Уровень</h2>
              <div className="flex gap-2">
                <select value={lvlName} onChange={(e) => setLvlName(e.target.value)} className="select">
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
                <button onClick={() => wrap(() => api.post(`/courses/${selected}/levels`, { name: lvlName }), "Уровень добавлен")} className="btn btn-ghost">Добавить</button>
              </div>
            </section>

            <section className="card p-5">
              <h2 className="section-title mb-3">Модуль</h2>
              <div className="flex flex-wrap gap-2">
                <select value={modLevel} onChange={(e) => setModLevel(e.target.value ? Number(e.target.value) : "")} className="select w-36">
                  <option value="">— уровень —</option>
                  {tree.levels.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
                <input placeholder="Название" value={modTitle} onChange={(e) => setModTitle(e.target.value)} className="input flex-1" />
                <button
                  onClick={() => wrap(async () => {
                    if (typeof modLevel !== "number" || !modTitle) return;
                    await api.post(`/levels/${modLevel}/modules`, { title: modTitle });
                    setModTitle("");
                  }, "Модуль добавлен")}
                  className="btn btn-ghost"
                >
                  Добавить
                </button>
              </div>
            </section>
          </div>

          <section className="card p-5">
            <h2 className="section-title mb-3">Урок</h2>
            <div className="mb-3 flex flex-wrap gap-2">
              <select value={lesModule} onChange={(e) => setLesModule(e.target.value ? Number(e.target.value) : "")} className="select w-64">
                <option value="">— модуль —</option>
                {modules.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
              </select>
              <input placeholder="Название урока" value={lesTitle} onChange={(e) => setLesTitle(e.target.value)} className="input flex-1" />
            </div>
            <MarkdownEditor value={lesContent} onChange={setLesContent} />
            <button
              onClick={() => wrap(async () => {
                if (typeof lesModule !== "number" || !lesTitle) return;
                await api.post(`/modules/${lesModule}/lessons`, { title: lesTitle, content_md: lesContent });
                setLesTitle("");
              }, "Урок сохранён")}
              className="btn btn-primary mt-3"
            >
              Сохранить урок
            </button>
          </section>

          <section className="card p-5">
            <h2 className="section-title mb-3">Редактировать урок</h2>
            <div className="mb-3 flex flex-wrap gap-2">
              <select value={editLesson} onChange={(e) => setEditLesson(e.target.value ? Number(e.target.value) : "")} className="select w-64">
                <option value="">— выберите урок —</option>
                {lessonsFlat.map((l) => <option key={l.id} value={l.id}>{l.label}</option>)}
              </select>
              {typeof editLesson === "number" && (
                <input placeholder="Название" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className="input flex-1" />
              )}
            </div>
            {typeof editLesson === "number" && (
              <>
                <MarkdownEditor value={editContent} onChange={setEditContent} />
                <button
                  onClick={() => wrap(async () => {
                    await api.patch(`/lessons/${editLesson}`, { title: editTitle, content_md: editContent });
                  }, "Урок обновлён")}
                  className="btn btn-primary mt-3"
                >
                  Сохранить изменения
                </button>
              </>
            )}
          </section>

          <section>
            <h2 className="section-title mb-2">Структура</h2>
            <div className="card space-y-2 p-4">
              {tree.levels.map((l) => (
                <div key={l.id}>
                  <div className="font-medium text-[var(--primary)]">{l.name}</div>
                  {l.modules.map((m) => (
                    <div key={m.id} className="muted ml-4 text-sm">
                      • {m.title} <span className="opacity-70">({m.lessons.map((x) => x.title).join(", ") || "нет уроков"})</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </section>

          <div>
            <h2 className="section-title mb-2">Вопросы и квизы</h2>
            <TeacherContent tree={tree} />
          </div>
        </>
      )}
    </div>
  );
}
