import "./globals.css";
import "highlight.js/styles/github-dark.css";
import type { Metadata } from "next";

import Nav from "@/components/Nav";

import Providers from "./providers";

export const metadata: Metadata = {
  title: "onproger — учись программировать по-настоящему",
  description: "Онлайн-школа C++ и Python: учебники, практика на задачах Codeforces и экзамены с разбором.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <Providers>
          <div className="flex min-h-screen flex-col">
            <Nav />
            <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8">{children}</main>
            <footer className="border-t border-[var(--border)]">
              <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-8 text-sm">
                <div className="flex items-center gap-2 font-black">
                  <span className="grid h-7 w-7 place-items-center rounded-lg bg-[var(--ink)] font-mono text-xs text-[var(--accent)]">&lt;/&gt;</span>
                  onproger
                </div>
                <span className="muted">C++ и Python · учебники · задачи · экзамены</span>
                <span className="muted">© 2026 onproger</span>
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
