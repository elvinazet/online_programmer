"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth";

export default function Nav() {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <nav className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
      <div className="flex items-center gap-4">
        <Link href="/" className="font-semibold text-indigo-700">
          Online Programmer
        </Link>
        {user && (
          <>
            <Link href="/" className="text-sm text-slate-600 hover:text-slate-900">
              Курсы
            </Link>
            <Link href="/problems" className="text-sm text-slate-600 hover:text-slate-900">
              Задачи
            </Link>
            <Link href="/exams" className="text-sm text-slate-600 hover:text-slate-900">
              Экзамены
            </Link>
            <Link href="/me" className="text-sm text-slate-600 hover:text-slate-900">
              Профиль
            </Link>
          </>
        )}
        {user?.role === "teacher" && (
          <Link href="/teach" className="text-sm text-slate-600 hover:text-slate-900">
            Преподавание
          </Link>
        )}
      </div>
      <div className="flex items-center gap-3 text-sm">
        {user ? (
          <>
            <span className="text-slate-500">
              {user.email} · {user.role === "teacher" ? "учитель" : "ученик"}
            </span>
            <button
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="rounded border border-slate-300 px-3 py-1 hover:bg-slate-50"
            >
              Выйти
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="hover:text-slate-900">
              Вход
            </Link>
            <Link href="/register" className="rounded bg-indigo-600 px-3 py-1 text-white">
              Регистрация
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
