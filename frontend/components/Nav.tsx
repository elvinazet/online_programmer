"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth";

import ThemeToggle from "./ThemeToggle";

const LINKS = [
  { href: "/", label: "Курсы" },
  { href: "/problems", label: "Задачи" },
  { href: "/exams", label: "Экзамены" },
];

export default function Nav() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <nav className="nav-blur sticky top-0 z-30 border-b">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-5 py-3">
        <div className="flex items-center gap-1">
          <Link href="/" className="mr-3 flex items-center gap-2 font-semibold">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-[var(--primary)] text-[var(--primary-fg)]">
              ⟨⟩
            </span>
            <span className="hidden sm:inline">Online Programmer</span>
          </Link>
          {user &&
            LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className={`rounded-lg px-3 py-1.5 text-sm transition ${
                  isActive(l.href) ? "bg-[var(--surface-2)] font-medium" : "muted hover:text-[var(--text)]"
                }`}
              >
                {l.label}
              </Link>
            ))}
          {user?.role === "teacher" && (
            <Link
              href="/teach"
              className={`rounded-lg px-3 py-1.5 text-sm transition ${
                isActive("/teach") ? "bg-[var(--surface-2)] font-medium" : "muted hover:text-[var(--text)]"
              }`}
            >
              Преподавание
            </Link>
          )}
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {user ? (
            <>
              <Link
                href="/me"
                className="hidden items-center gap-2 rounded-lg px-2 py-1 text-sm hover:bg-[var(--surface-2)] sm:flex"
              >
                <span className="grid h-7 w-7 place-items-center rounded-full bg-[var(--surface-2)] text-xs font-semibold uppercase">
                  {user.email.slice(0, 2)}
                </span>
                <span className="badge">{user.role === "teacher" ? "учитель" : "ученик"}</span>
              </Link>
              <button
                onClick={async () => {
                  await logout();
                  router.push("/login");
                }}
                className="btn btn-ghost btn-sm"
              >
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn btn-ghost btn-sm">
                Вход
              </Link>
              <Link href="/register" className="btn btn-primary btn-sm">
                Регистрация
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
