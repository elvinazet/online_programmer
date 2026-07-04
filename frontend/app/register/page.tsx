"use client";
import Link from "next/link";
import { useState } from "react";

import { Icon } from "@/components/Icon";
import { Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import type { Role } from "@/lib/types";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("student");
  const [extra, setExtra] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.post("/auth/register", {
        email,
        password,
        role,
        display_name: role === "teacher" ? extra || null : null,
        codeforces_handle: role === "student" ? extra || null : null,
      });
      setDone(true);
    } catch (err: any) {
      setError(err.message || "Ошибка регистрации");
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="mx-auto mt-8 max-w-sm">
        <div className="card p-7 text-center">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[var(--surface-2)] text-[var(--primary)]">
            <Icon name="mail" className="h-7 w-7" />
          </div>
          <h1 className="page-title mt-3">Почти готово</h1>
          <p className="muted mt-2 text-sm">
            Мы отправили письмо для подтверждения email. В dev-режиме ссылка печатается
            в лог контейнера <code>api</code>.
          </p>
          <Link href="/login" className="link mt-4 inline-block">Перейти ко входу</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto mt-8 max-w-sm">
      <div className="card p-7">
        <h1 className="page-title mb-1">Создать аккаунт</h1>
        <p className="muted mb-5 text-sm">Начните учиться уже сегодня.</p>
        <form onSubmit={onSubmit} className="space-y-3">
          <div>
            <label className="label">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input" placeholder="you@example.com" />
          </div>
          <div>
            <label className="label">Пароль</label>
            <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} className="input" placeholder="минимум 8 символов" />
          </div>
          <div>
            <label className="label">Роль</label>
            <select value={role} onChange={(e) => setRole(e.target.value as Role)} className="select">
              <option value="student">Ученик</option>
              <option value="teacher">Учитель</option>
            </select>
          </div>
          <div>
            <label className="label">{role === "teacher" ? "Имя (необязательно)" : "Codeforces-хэндл (необязательно)"}</label>
            <input type="text" value={extra} onChange={(e) => setExtra(e.target.value)} className="input" />
          </div>
          {error && <div className="badge badge-danger w-full justify-start px-3 py-2">{error}</div>}
          <button disabled={busy} className="btn btn-primary w-full">
            {busy && <Spinner />} Зарегистрироваться
          </button>
        </form>
        <p className="muted mt-4 text-sm">
          Уже есть аккаунт? <Link href="/login" className="link">Войти</Link>
        </p>
      </div>
    </div>
  );
}
