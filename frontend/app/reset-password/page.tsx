"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export default function ResetPasswordPage() {
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get("token") || "");
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage("");
    setBusy(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      setDone(true);
    } catch (err: any) {
      setMessage(err.message || "Ошибка сброса пароля");
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="mx-auto max-w-sm text-center">
        <h1 className="mb-2 text-xl font-semibold">Пароль обновлён</h1>
        <Link href="/login" className="text-indigo-600 underline">
          Войти с новым паролем
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-4 text-xl font-semibold">Новый пароль</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <input
          type="password"
          required
          minLength={8}
          placeholder="Новый пароль (мин. 8 символов)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2"
        />
        {message && <p className="text-sm text-rose-600">{message}</p>}
        <button
          disabled={busy || !token}
          className="w-full rounded bg-indigo-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {busy ? "Сохраняем…" : "Сохранить пароль"}
        </button>
        {!token && <p className="text-sm text-rose-600">Токен не найден в ссылке.</p>}
      </form>
    </div>
  );
}
