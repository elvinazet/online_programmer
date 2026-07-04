"use client";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { CourseTree, QuestionType, TeacherQuestion } from "@/lib/types";

import QuestionForm from "./QuestionForm";
import { useToast } from "./Toast";

const TYPE: Record<QuestionType, string> = {
  single_choice: "один",
  multiple_choice: "неск.",
  short_answer: "текст",
  code_output: "вывод",
};

export default function TeacherContent({ tree }: { tree: CourseTree }) {
  const toast = useToast();
  const modules = tree.levels.flatMap((l) => l.modules.map((m) => ({ id: m.id, label: `${l.name} / ${m.title}` })));
  const lessons = tree.levels.flatMap((l) =>
    l.modules.flatMap((m) => m.lessons.map((les) => ({ id: les.id, moduleId: m.id, label: `${m.title} / ${les.title}` }))),
  );

  const [moduleId, setModuleId] = useState<number | "">("");
  const [moduleQuestions, setModuleQuestions] = useState<TeacherQuestion[]>([]);
  const [lessonId, setLessonId] = useState<number | "">("");
  const [quiz, setQuiz] = useState<TeacherQuestion[]>([]);
  const [attachOptions, setAttachOptions] = useState<TeacherQuestion[]>([]);

  const loadModuleQuestions = useCallback(async (id: number) => {
    setModuleQuestions(await api.get<TeacherQuestion[]>(`/modules/${id}/questions`));
  }, []);
  const loadQuiz = useCallback(async (id: number) => {
    setQuiz(await api.get<TeacherQuestion[]>(`/lessons/${id}/questions`));
  }, []);

  useEffect(() => {
    if (typeof moduleId === "number") loadModuleQuestions(moduleId).catch(() => {});
    else setModuleQuestions([]);
  }, [moduleId, loadModuleQuestions]);

  useEffect(() => {
    if (typeof lessonId === "number") loadQuiz(lessonId).catch(() => {});
    else setQuiz([]);
  }, [lessonId, loadQuiz]);

  const lessonModuleId = typeof lessonId === "number" ? lessons.find((l) => l.id === lessonId)?.moduleId : undefined;
  useEffect(() => {
    if (lessonModuleId) api.get<TeacherQuestion[]>(`/modules/${lessonModuleId}/questions`).then(setAttachOptions).catch(() => setAttachOptions([]));
    else setAttachOptions([]);
  }, [lessonModuleId, quiz]);

  const quizIds = new Set(quiz.map((q) => q.id));
  const attachable = attachOptions.filter((q) => !quizIds.has(q.id));

  async function attach(qid: number) {
    try {
      await api.post(`/lessons/${lessonId}/questions`, { question_id: qid });
      toast.success("Добавлено в квиз");
      if (typeof lessonId === "number") loadQuiz(lessonId);
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <section className="card p-5">
        <h2 className="section-title mb-3">Банк вопросов модуля</h2>
        <select className="select mb-3" value={moduleId} onChange={(e) => setModuleId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">— модуль —</option>
          {modules.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
        </select>
        {typeof moduleId === "number" && (
          <>
            <QuestionForm moduleId={moduleId} onCreated={() => loadModuleQuestions(moduleId)} />
            {moduleQuestions.length > 0 && (
              <div className="mt-4">
                <div className="label">Вопросы модуля ({moduleQuestions.length})</div>
                {moduleQuestions.map((q) => (
                  <div key={q.id} className="table-row flex items-center gap-2 py-1.5 text-sm last:border-0">
                    <span className="badge">{TYPE[q.type]}</span>
                    <span className="flex-1 truncate">{q.prompt_md}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </section>

      <section className="card p-5">
        <h2 className="section-title mb-3">Мини-квиз урока</h2>
        <select className="select mb-3" value={lessonId} onChange={(e) => setLessonId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">— урок —</option>
          {lessons.map((l) => <option key={l.id} value={l.id}>{l.label}</option>)}
        </select>
        {typeof lessonId === "number" && (
          <div className="space-y-4">
            <div>
              <div className="label">В квизе ({quiz.length})</div>
              {quiz.length === 0 ? (
                <p className="muted text-sm">Пока пусто.</p>
              ) : (
                quiz.map((q) => <div key={q.id} className="table-row py-1.5 text-sm last:border-0">{q.prompt_md}</div>)
              )}
            </div>
            <div>
              <div className="label">Добавить из банка модуля</div>
              {attachable.length === 0 ? (
                <p className="muted text-sm">Нет доступных вопросов — создайте их в банке модуля слева.</p>
              ) : (
                attachable.map((q) => (
                  <div key={q.id} className="flex items-center gap-2 py-1 text-sm">
                    <span className="flex-1 truncate">{q.prompt_md}</span>
                    <button onClick={() => attach(q.id)} className="btn btn-ghost btn-sm">+ в квиз</button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
