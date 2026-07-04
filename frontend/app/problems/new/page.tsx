"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useToast } from "@/components/Toast";
import { PageHeader, PageLoader } from "@/components/ui";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Problem } from "@/lib/types";

export default function NewProblemPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const toast = useToast();

  const [title, setTitle] = useState("");
  const [statement, setStatement] = useState("");
  const [rating, setRating] = useState("");
  const [tags, setTags] = useState("");
  const [timeLimit, setTimeLimit] = useState("2000");
  const [memLimit, setMemLimit] = useState("256");

  const [created, setCreated] = useState<Problem | null>(null);
  const [tests, setTests] = useState<{ input: string; expected: string; sample: boolean }[]>([]);
  const [tin, setTin] = useState("");
  const [tout, setTout] = useState("");
  const [tsample, setTsample] = useState(true);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role !== "teacher") router.replace("/problems");
  }, [user, loading, router]);

  if (loading || !user) return <PageLoader />;

  async function createProblem() {
    if (!title.trim()) {
      toast.error("Введите название");
      return;
    }
    try {
      const p = await api.post<Problem>("/problems", {
        title,
        statement_md: statement || null,
        rating: rating ? Number(rating) : null,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        time_limit_ms: Number(timeLimit),
        memory_limit_mb: Number(memLimit),
      });
      setCreated(p);
      toast.success(`Задача создана (id ${p.id})`);
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  async function addTest() {
    if (!created) return;
    if (!tin.trim() && !tout.trim()) {
      toast.error("Заполните тест");
      return;
    }
    try {
      await api.post(`/problems/${created.id}/tests`, {
        input: tin,
        expected_output: tout,
        is_sample: tsample,
      });
      setTests((t) => [...t, { input: tin, expected: tout, sample: tsample }]);
      setTin("");
      setTout("");
      toast.success("Тест добавлен");
    } catch (e: any) {
      toast.error(e.message);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Новая задача"
        subtitle="Авторская задача с тестами для практики и экзаменов"
        actions={<Link href="/problems" className="btn btn-ghost btn-sm">← Задачи</Link>}
      />

      <section className="card space-y-3 p-5">
        <h2 className="section-title">Условие</h2>
        <input placeholder="Название" value={title} onChange={(e) => setTitle(e.target.value)} className="input" disabled={!!created} />
        <textarea placeholder="Условие (Markdown)" value={statement} onChange={(e) => setStatement(e.target.value)} className="input h-28" disabled={!!created} />
        <div className="flex flex-wrap gap-2">
          <input type="number" placeholder="рейтинг" value={rating} onChange={(e) => setRating(e.target.value)} className="input w-32" disabled={!!created} />
          <input placeholder="теги через запятую" value={tags} onChange={(e) => setTags(e.target.value)} className="input flex-1" disabled={!!created} />
          <input type="number" placeholder="время, мс" value={timeLimit} onChange={(e) => setTimeLimit(e.target.value)} className="input w-32" disabled={!!created} />
          <input type="number" placeholder="память, МБ" value={memLimit} onChange={(e) => setMemLimit(e.target.value)} className="input w-32" disabled={!!created} />
        </div>
        {!created ? (
          <button onClick={createProblem} className="btn btn-primary">Создать задачу</button>
        ) : (
          <div className="badge badge-success px-3 py-2">Задача создана · id {created.id} — теперь добавьте тесты</div>
        )}
      </section>

      {created && (
        <section className="card space-y-3 p-5">
          <h2 className="section-title">Тесты ({tests.length})</h2>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <textarea placeholder="Ввод (stdin)" value={tin} onChange={(e) => setTin(e.target.value)} className="input h-24 font-mono" />
            <textarea placeholder="Ожидаемый вывод" value={tout} onChange={(e) => setTout(e.target.value)} className="input h-24 font-mono" />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={tsample} onChange={(e) => setTsample(e.target.checked)} /> показывать как пример в условии
          </label>
          <div className="flex gap-2">
            <button onClick={addTest} className="btn btn-primary">Добавить тест</button>
            <Link href={`/problems/${created.id}`} className="btn btn-ghost">Открыть задачу</Link>
          </div>
          {tests.length > 0 && (
            <div className="mt-2 space-y-1">
              {tests.map((t, i) => (
                <div key={i} className="table-row flex gap-3 py-1.5 text-sm last:border-0">
                  <span className="badge">{t.sample ? "пример" : "скрытый"}</span>
                  <code className="muted flex-1 truncate">in: {t.input.trim()} → out: {t.expected.trim()}</code>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
