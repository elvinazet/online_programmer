"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export default function VerifyEmailPage() {
  const [state, setState] = useState<"pending" | "ok" | "error">("pending");
  const [message, setMessage] = useState("Подтверждаем email…");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
      setState("error");
      setMessage("Токен не найден в ссылке.");
      return;
    }
    api
      .post<{ message: string }>("/auth/verify-email", { token })
      .then((r) => {
        setState("ok");
        setMessage(r.message);
      })
      .catch((e) => {
        setState("error");
        setMessage(e.message || "Не удалось подтвердить email");
      });
  }, []);

  return (
    <div className="mx-auto max-w-sm text-center">
      <h1 className="mb-3 text-xl font-semibold">Подтверждение email</h1>
      <p className={state === "error" ? "text-rose-600" : "text-slate-700"}>{message}</p>
      {state === "ok" && (
        <Link href="/login" className="mt-4 inline-block text-indigo-600 underline">
          Перейти ко входу
        </Link>
      )}
    </div>
  );
}
