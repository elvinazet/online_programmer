"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth";

const LINKS = [
  { href: "/courses", label: "Курсы" },
  { href: "/problems", label: "Задачи" },
  { href: "/exams", label: "Экзамены" },
];

export default function Nav() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isActive = (href: string) => pathname.startsWith(href);

  return (
    <nav className="nav-blur sticky top-0 z-30 border-b border-[var(--border)]">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-3">
        <div className="flex items-center gap-1">
          <Link href="/" className="mr-3 flex items-center gap-2 text-lg font-black tracking-tight">
            <span className="grid h-8 w-8 place-items-center rounded-xl bg-[var(--ink)] font-mono text-sm text-[var(--accent)]">
              &lt;/&gt;
            </span>
            <span>onproger</span>
          </Link>
          {user && (
            <div className="hidden items-center gap-1 md:flex">
              {LINKS.map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`rounded-full px-3.5 py-1.5 text-sm font-bold transition ${
                    isActive(l.href) ? "bg-[var(--accent)] text-[var(--accent-fg)]" : "muted hover:text-[var(--text)]"
                  }`}
                >
                  {l.label}
                </Link>
              ))}
              {user.role === "teacher" && (
                <Link
                  href="/teach"
                  className={`rounded-full px-3.5 py-1.5 text-sm font-bold transition ${
                    isActive("/teach") ? "bg-[var(--accent)] text-[var(--accent-fg)]" : "muted hover:text-[var(--text)]"
                  }`}
                >
                  Преподавание
                </Link>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {user ? (
            <>
              <Link
                href="/me"
                className="hidden items-center gap-2 rounded-full px-2 py-1 text-sm hover:bg-[var(--surface-2)] sm:flex"
              >
                <span className="grid h-8 w-8 place-items-center rounded-full bg-[var(--primary)] text-xs font-black uppercase text-white">
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
              <Link href="/register" className="btn btn-accent btn-sm">
                Начать бесплатно
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
