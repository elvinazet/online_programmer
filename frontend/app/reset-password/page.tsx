"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "@/components/Icon";
import { Spinner } from "@/components/ui";
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
      <div className="mx-auto mt-8 max-w-sm">
        <div className="card p-7 text-center">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[var(--success-soft)] text-[var(--success)]">
            <Icon name="check-badge" className="h-7 w-7" />
          </div>
          <h1 className="page-title mt-3">Пароль обновлён</h1>
          <Link href="/login" className="link mt-4 inline-block">Войти с новым паролем</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto mt-8 max-w-sm">
      <div className="card p-7">
        <h1 className="page-title mb-5">Новый пароль</h1>
        <form onSubmit={onSubmit} className="space-y-3">
          <input type="password" required minLength={8} placeholder="Новый пароль (мин. 8)" value={password} onChange={(e) => setPassword(e.target.value)} className="input" />
          {message && <div className="badge badge-danger w-full justify-start px-3 py-2">{message}</div>}
          <button disabled={busy || !token} className="btn btn-primary w-full">
            {busy && <Spinner />} Сохранить пароль
          </button>
          {!token && <p className="badge badge-warning w-full justify-start px-3 py-2">Токен не найден в ссылке.</p>}
        </form>
      </div>
    </div>
  );
}
