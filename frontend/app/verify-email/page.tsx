"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Spinner } from "@/components/ui";
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
    <div className="mx-auto mt-8 max-w-sm">
      <div className="card p-7 text-center">
        <div className="text-3xl">{state === "ok" ? "✅" : state === "error" ? "⚠️" : "⏳"}</div>
        <h1 className="page-title mt-2">Подтверждение email</h1>
        <p className={`mt-2 text-sm ${state === "error" ? "badge-danger badge w-full justify-center py-2" : "muted"}`}>
          {state === "pending" && <Spinner />} {message}
        </p>
        {state === "ok" && <Link href="/login" className="link mt-4 inline-block">Перейти ко входу</Link>}
      </div>
    </div>
  );
}
