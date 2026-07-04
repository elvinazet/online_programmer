"use client";
import Link from "next/link";

import Burst from "./Burst";

const FEATURES = [
  {
    icon: "📚",
    title: "Интерактивные учебники",
    text: "C++ и Python: курс → уровень → модуль → урок. Markdown с подсветкой кода, примеры с запуском прямо в браузере и мини-квиз в конце каждого урока.",
  },
  {
    icon: "🧩",
    title: "Практика на Codeforces",
    text: "Подбор задач по темам и рейтингу под твой уровень. Пишешь решение в редакторе — оно проверяется на тестах в изолированном sandbox, вердикт сразу.",
  },
  {
    icon: "🏁",
    title: "Экзамены на уровень",
    text: "Переход на следующий уровень — через контест на время: практика (задачи) + теория. Серверный таймер и честный порог сдачи.",
  },
  {
    icon: "🔍",
    title: "Разбор результатов",
    text: "После каждого экзамена — карта сильных и слабых тем и персональный план: какие уроки повторить и какие задачи прорешать.",
  },
];

const LEVELS = ["Beginner", "Intermediate", "Advanced"];

export default function Landing() {
  return (
    <div className="space-y-14">
      {/* HERO */}
      <section className="relative grid grid-cols-1 items-center gap-6 lg:grid-cols-[1.05fr_.95fr]">
        <div className="relative">
          <p className="eyebrow">Онлайн-школа программирования</p>
          <h1 className="mt-3 text-4xl font-black leading-[1.02] tracking-tight sm:text-5xl">
            Пиши код, решай задачи,{" "}
            <span className="hl">расти по уровням</span>
          </h1>
          <p className="muted mt-4 max-w-xl text-lg">
            C++ и Python с нуля до продвинутого. Интерактивные учебники, практика на
            задачах Codeforces с проверкой прямо в браузере и экзамены с детальным разбором.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/register" className="btn btn-accent">Начать бесплатно</Link>
            <Link href="/login" className="btn btn-ghost">Уже учусь — войти</Link>
          </div>
          <div className="mt-6 flex flex-wrap gap-2">
            {["Учебники", "Задачи Codeforces", "Экзамены", "Разбор по темам"].map((c) => (
              <span key={c} className="badge badge-primary">{c}</span>
            ))}
          </div>
        </div>

        {/* code card */}
        <div className="relative">
          <Burst points={12} inner={0.42} className="absolute -right-4 -top-6 h-16 w-16 text-[var(--accent)]" />
          <div className="card overflow-hidden p-0">
            <div className="flex items-center gap-2 border-b border-[var(--border)] px-4 py-2.5">
              <span className="h-3 w-3 rounded-full bg-[var(--danger)]" />
              <span className="h-3 w-3 rounded-full bg-[var(--warning)]" />
              <span className="h-3 w-3 rounded-full bg-[var(--success)]" />
              <span className="muted ml-2 text-xs">solution.py</span>
            </div>
            <pre className="overflow-x-auto bg-[#12121a] px-4 py-4 text-sm leading-relaxed text-slate-100">
{`a, b = map(int, input().split())
print(a + b)`}
            </pre>
            <div className="flex items-center justify-between px-4 py-3">
              <span className="btn btn-accent btn-sm">▶ Запустить</span>
              <span className="badge badge-success">✓ Принято · 2/2 тестов</span>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section>
        <h2 className="section-title mb-1 text-2xl">Чему и как учим</h2>
        <p className="muted mb-6">Всё, что нужно, чтобы дойти от первой строчки кода до серьёзных задач.</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {FEATURES.map((f) => (
            <div key={f.title} className="card p-6">
              <div className="text-3xl">{f.icon}</div>
              <h3 className="mt-3 text-lg font-extrabold">{f.title}</h3>
              <p className="muted mt-1 text-sm">{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* PROGRESS (dark accent band) */}
      <section className="relative overflow-hidden rounded-[26px] bg-[var(--ink)] p-8 text-white sm:p-10">
        <Burst points={16} inner={0.7} className="absolute -left-8 -top-8 h-32 w-32 text-white/5" />
        <p className="eyebrow" style={{ color: "var(--accent)" }}>Виден каждый шаг</p>
        <h2 className="mt-2 text-2xl font-black sm:text-3xl">Прогресс, который мотивирует</h2>
        <p className="mt-2 max-w-2xl text-white/70">
          Отмечаем серию дней с решениями, копим статистику по темам и сложности,
          храним историю экзаменов. Новый уровень открывается только после сдачи —
          как в настоящей игре.
        </p>
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { big: "🔥", t: "streak за активность" },
            { big: "📈", t: "статистика по темам" },
            { big: "🏆", t: "история экзаменов" },
            { big: "🔓", t: "уровни открываются" },
          ].map((s) => (
            <div key={s.t} className="rounded-2xl bg-white/5 p-4 text-center">
              <div className="text-2xl">{s.big}</div>
              <div className="mt-1 text-sm text-white/75">{s.t}</div>
            </div>
          ))}
        </div>
      </section>

      {/* LANGUAGES / LEVELS */}
      <section>
        <h2 className="section-title mb-1 text-2xl">Два языка, три уровня</h2>
        <p className="muted mb-6">От основ до продвинутого — с экзаменом на каждом переходе.</p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[
            { lang: "Python", icon: "🐍", text: "От переменных и циклов до нейросетей и автоматизации." },
            { lang: "C++", icon: "＋＋", text: "От синтаксиса до алгоритмов и олимпиадных задач." },
          ].map((c) => (
            <div key={c.lang} className="card p-6">
              <div className="flex items-center gap-3">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-[var(--surface-2)] text-lg font-black">{c.icon}</span>
                <div>
                  <div className="text-lg font-extrabold">{c.lang}</div>
                  <div className="muted text-sm">{c.text}</div>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {LEVELS.map((lvl, i) => (
                  <span key={lvl} className={i === 0 ? "badge badge-accent" : "badge"}>{lvl}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* TEACHERS */}
      <section className="card grid grid-cols-1 gap-6 p-8 sm:p-10 lg:grid-cols-[1fr_.9fr]">
        <div>
          <p className="eyebrow">Для преподавателей</p>
          <h2 className="mt-2 text-2xl font-black sm:text-3xl">Ведите свою группу</h2>
          <p className="muted mt-2">
            Собственный конструктор учебников, квизов, задач и экзаменов. Группы учеников,
            назначение задач и глав, прогресс группы и разбор по темам — всё в одном месте.
          </p>
          <Link href="/register" className="btn btn-primary mt-5">Создать аккаунт учителя</Link>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {[
            "Конструктор учебников, квизов и экзаменов",
            "Группы учеников и назначение задач/глав",
            "Прогресс группы и разбор западающих тем",
          ].map((t) => (
            <div key={t} className="flex items-center gap-3 rounded-2xl surface-2 p-4">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[var(--accent)] font-black text-[var(--accent-fg)]">✓</span>
              <span className="text-sm font-semibold">{t}</span>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden rounded-[26px] bg-[var(--primary)] p-10 text-center text-white">
        <Burst points={10} inner={0.4} className="float absolute right-8 top-6 h-16 w-16 text-[var(--accent)]" />
        <h2 className="text-3xl font-black sm:text-4xl">Готов написать первый код?</h2>
        <p className="mx-auto mt-2 max-w-xl text-white/80">
          Регистрация бесплатна. Начни с интерактивного урока и первой задачи уже сегодня.
        </p>
        <Link href="/register" className="btn btn-accent mt-6 text-base">Начать бесплатно</Link>
      </section>
    </div>
  );
}
