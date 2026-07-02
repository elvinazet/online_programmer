"use client";
import Link from "next/link";
import { useState } from "react";

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
      <div className="mx-auto max-w-sm">
        <h1 className="mb-2 text-xl font-semibold">Почти готово</h1>
        <p className="text-slate-600">
          Мы отправили письмо для подтверждения email. В dev-режиме ссылка печатается
          в лог контейнера <code>api</code>. После подтверждения{" "}
          <Link href="/login" className="text-indigo-600 underline">
            войдите
          </Link>
          .
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-4 text-xl font-semibold">Регистрация</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2"
        />
        <input
          type="password"
          required
          minLength={8}
          placeholder="Пароль (мин. 8 символов)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as Role)}
          className="w-full rounded border border-slate-300 px-3 py-2"
        >
          <option value="student">Ученик</option>
          <option value="teacher">Учитель</option>
        </select>
        <input
          type="text"
          placeholder={role === "teacher" ? "Имя (необязательно)" : "Codeforces-хэндл (необязательно)"}
          value={extra}
          onChange={(e) => setExtra(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2"
        />
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button
          disabled={busy}
          className="w-full rounded bg-indigo-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {busy ? "Регистрируем…" : "Зарегистрироваться"}
        </button>
      </form>
      <p className="mt-3 text-sm text-slate-600">
        Уже есть аккаунт?{" "}
        <Link href="/login" className="text-indigo-600 underline">
          Войти
        </Link>
      </p>
    </div>
  );
}
