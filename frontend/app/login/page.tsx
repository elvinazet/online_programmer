"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Ошибка входа");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-4 text-xl font-semibold">Вход</h1>
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
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2"
        />
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button
          disabled={busy}
          className="w-full rounded bg-indigo-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {busy ? "Входим…" : "Войти"}
        </button>
      </form>
      <div className="mt-3 flex justify-between text-sm text-slate-600">
        <Link href="/register" className="hover:text-slate-900">
          Регистрация
        </Link>
        <Link href="/forgot-password" className="hover:text-slate-900">
          Забыли пароль?
        </Link>
      </div>
    </div>
  );
}
