"use client";
import Link from "next/link";
import { useState } from "react";

import { Spinner } from "@/components/ui";
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
    <div className="mx-auto mt-8 max-w-sm">
      <div className="card p-7">
        <h1 className="page-title mb-1">Восстановление пароля</h1>
        <p className="muted mb-5 text-sm">Пришлём ссылку для сброса на email.</p>
        <form onSubmit={onSubmit} className="space-y-3">
          <input type="email" required placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="input" />
          <button disabled={busy} className="btn btn-primary w-full">
            {busy && <Spinner />} Отправить ссылку
          </button>
        </form>
        {message && <p className="muted mt-3 text-sm">{message}</p>}
        <Link href="/login" className="link mt-4 inline-block text-sm">← Ко входу</Link>
      </div>
    </div>
  );
}
