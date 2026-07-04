"use client";
import { useState } from "react";

import { Icon } from "@/components/Icon";
import { useToast } from "@/components/Toast";
import { api } from "@/lib/api";
import type { QuestionType } from "@/lib/types";

const TYPE_LABELS: Record<QuestionType, string> = {
  single_choice: "Один вариант",
  multiple_choice: "Несколько вариантов",
  short_answer: "Короткий ответ",
  code_output: "Что выведет код",
};

export default function QuestionForm({
  moduleId,
  onCreated,
}: {
  moduleId: number;
  onCreated?: () => void;
}) {
  const toast = useToast();
  const [type, setType] = useState<QuestionType>("single_choice");
  const [prompt, setPrompt] = useState("");
  const [options, setOptions] = useState<string[]>(["", ""]);
  const [correctSingle, setCorrectSingle] = useState(0);
  const [correctMulti, setCorrectMulti] = useState<number[]>([]);
  const [accepted, setAccepted] = useState<string[]>([""]);
  const [explanation, setExplanation] = useState("");
  const [busy, setBusy] = useState(false);

  const isChoice = type === "single_choice" || type === "multiple_choice";

  function reset() {
    setPrompt("");
    setOptions(["", ""]);
    setCorrectSingle(0);
    setCorrectMulti([]);
    setAccepted([""]);
    setExplanation("");
  }

  async function submit() {
    if (!prompt.trim()) {
      toast.error("Введите текст вопроса");
      return;
    }
    let correct_answer: Record<string, unknown>;
    if (type === "single_choice") correct_answer = { correct: correctSingle };
    else if (type === "multiple_choice") correct_answer = { correct: [...correctMulti].sort((a, b) => a - b) };
    else correct_answer = { accepted: accepted.map((a) => a.trim()).filter(Boolean) };

    setBusy(true);
    try {
      await api.post(`/modules/${moduleId}/questions`, {
        type,
        prompt_md: prompt,
        options: isChoice ? options.map((o) => o.trim()).filter(Boolean) : null,
        correct_answer,
        explanation_md: explanation || null,
      });
      toast.success("Вопрос добавлен в банк");
      reset();
      onCreated?.();
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <select value={type} onChange={(e) => setType(e.target.value as QuestionType)} className="select w-56">
          {Object.entries(TYPE_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>

      <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Текст вопроса (Markdown)" className="input h-20" />

      {isChoice && (
        <div className="space-y-2">
          <div className="label">Варианты (отметьте правильный{type === "multiple_choice" ? "е" : ""})</div>
          {options.map((opt, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <input
                type={type === "single_choice" ? "radio" : "checkbox"}
                name="correct-opt"
                checked={type === "single_choice" ? correctSingle === idx : correctMulti.includes(idx)}
                onChange={() =>
                  type === "single_choice"
                    ? setCorrectSingle(idx)
                    : setCorrectMulti((m) => (m.includes(idx) ? m.filter((i) => i !== idx) : [...m, idx]))
                }
              />
              <input
                value={opt}
                onChange={(e) => setOptions((o) => o.map((x, i) => (i === idx ? e.target.value : x)))}
                placeholder={`Вариант ${idx + 1}`}
                className="input flex-1"
              />
              {options.length > 2 && (
                <button onClick={() => setOptions((o) => o.filter((_, i) => i !== idx))} className="btn btn-ghost btn-sm" aria-label="Удалить вариант"><Icon name="x" className="h-4 w-4" /></button>
              )}
            </div>
          ))}
          <button onClick={() => setOptions((o) => [...o, ""])} className="btn btn-ghost btn-sm">+ вариант</button>
        </div>
      )}

      {!isChoice && (
        <div className="space-y-2">
          <div className="label">Допустимые ответы</div>
          {accepted.map((a, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <input value={a} onChange={(e) => setAccepted((arr) => arr.map((x, i) => (i === idx ? e.target.value : x)))} placeholder="Ответ" className="input flex-1" />
              {accepted.length > 1 && (
                <button onClick={() => setAccepted((arr) => arr.filter((_, i) => i !== idx))} className="btn btn-ghost btn-sm" aria-label="Удалить ответ"><Icon name="x" className="h-4 w-4" /></button>
              )}
            </div>
          ))}
          <button onClick={() => setAccepted((arr) => [...arr, ""])} className="btn btn-ghost btn-sm">+ ответ</button>
        </div>
      )}

      <textarea value={explanation} onChange={(e) => setExplanation(e.target.value)} placeholder="Пояснение (необязательно)" className="input h-16" />

      <button onClick={submit} disabled={busy} className="btn btn-primary">Добавить вопрос</button>
    </div>
  );
}
