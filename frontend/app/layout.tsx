import "./globals.css";
import "highlight.js/styles/github-dark.css";
import type { Metadata } from "next";

import Nav from "@/components/Nav";

import Providers from "./providers";

export const metadata: Metadata = {
  title: "Online Programmer — школа C++ и Python",
  description: "Учебники, практика на задачах Codeforces и экзамены с разбором.",
};

const themeInit = `try{var t=localStorage.getItem('op_theme');if(t){document.documentElement.setAttribute('data-theme',t);}}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
        <Providers>
          <div className="flex min-h-screen flex-col">
            <Nav />
            <main className="mx-auto w-full max-w-5xl flex-1 px-5 py-8">{children}</main>
            <footer className="mx-auto w-full max-w-5xl px-5 py-8 text-center text-xs muted">
              Online Programmer · онлайн-школа программирования
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
