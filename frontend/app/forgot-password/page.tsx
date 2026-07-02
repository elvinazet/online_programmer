"use client";
import { useState } from "react";

import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await api.post<{ message: string }>("/auth/forgot-password", { email });
      setMessage(r.message);
    } catch (err: any) {
      setMessage(err.message || "Ошибка");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-4 text-xl font-semibold">Восстановление пароля</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2"
        />
        <button
          disabled={busy}
          className="w-full rounded bg-indigo-600 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {busy ? "Отправляем…" : "Отправить ссылку"}
        </button>
      </form>
      {message && <p className="mt-3 text-sm text-slate-600">{message}</p>}
    </div>
  );
}
