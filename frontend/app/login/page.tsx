"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Spinner } from "@/components/ui";
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
    <div className="mx-auto mt-8 max-w-sm">
      <div className="card p-7">
        <h1 className="page-title mb-1">С возвращением</h1>
        <p className="muted mb-5 text-sm">Войдите, чтобы продолжить обучение.</p>
        <form onSubmit={onSubmit} className="space-y-3">
          <div>
            <label className="label">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input" placeholder="you@example.com" />
          </div>
          <div>
            <label className="label">Пароль</label>
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="input" placeholder="••••••••" />
          </div>
          {error && <div className="badge badge-danger w-full justify-start px-3 py-2">{error}</div>}
          <button disabled={busy} className="btn btn-primary w-full">
            {busy && <Spinner />} Войти
          </button>
        </form>
        <div className="mt-4 flex justify-between text-sm">
          <Link href="/register" className="link">Регистрация</Link>
          <Link href="/forgot-password" className="link">Забыли пароль?</Link>
        </div>
      </div>
    </div>
  );
}
